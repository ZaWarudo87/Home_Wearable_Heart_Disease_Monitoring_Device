import os
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt


# ----------------------------------------------------------------------
# ST-segment specific filtering: 0.5–35 Hz band (high-pass + low-pass)
# ----------------------------------------------------------------------

def filter_for_st(sig, fs):
    """
    ST-segment oriented filter:
      - 3rd-order high-pass at 0.5 Hz
      - 3rd-order low-pass at 35 Hz
    """
    sig = np.asarray(sig, dtype=float)

    # High-pass 0.5 Hz
    hp_cut = 0.5      # Hz
    hp_N = 3
    Wn_hp = hp_cut * 2.0 / fs
    bhp, ahp = signal.butter(hp_N, Wn_hp, btype="highpass")
    sig_hp = signal.filtfilt(bhp, ahp, sig)

    # Low-pass 35 Hz
    lp_cut = 35.0     # Hz
    lp_N = 3
    Wn_lp = lp_cut * 2.0 / fs
    blp, alp = signal.butter(lp_N, Wn_lp, btype="lowpass")
    sig_bp = signal.filtfilt(blp, alp, sig_hp)

    return sig_bp


# ----------------------------------------------------------------------
# R-peak detection (same as your previous detector)
# ----------------------------------------------------------------------

def robust_r_peaks(sig_mV: np.ndarray, fs: float) -> np.ndarray:
    """
    Pan-Tompkins style R-peak detection with adaptive thresholds.

    Steps:
      - 2nd-order 5–20 Hz band-pass
      - derivative -> square -> moving window integration (~150 ms)
      - robust z-score thresholding on the integrated signal
      - peak refinement on the band-passed signal
      - merge peaks that are too close (refractory period)
    """
    # Band-pass to enhance QRS
    b, a = signal.butter(2, [5 / (fs / 2), 20 / (fs / 2)], btype="bandpass")
    x = signal.filtfilt(b, a, sig_mV)

    # Derivative -> square -> MWI (~150 ms)
    dx = np.diff(x, prepend=x[0])
    sq = dx * dx
    win = max(1, int(0.15 * fs))
    mwi = np.convolve(sq, np.ones(win) / win, mode="same")

    # Robust normalization (median + MAD)
    med = np.median(mwi)
    mad = np.median(np.abs(mwi - med)) + 1e-12
    z = (mwi - med) / mad

    refractory = int(0.28 * fs)  # 280 ms
    height = 3.0                 # z-units
    prom = 1.5                   # z-units

    peaks_mwi, _ = signal.find_peaks(
        z,
        distance=refractory,
        height=height,
        prominence=prom,
    )

    if peaks_mwi.size == 0:
        return peaks_mwi

    # Refine peaks on band-passed signal (±80 ms)
    refine_win = int(0.08 * fs)
    refined = []
    for p in peaks_mwi:
        lo = max(0, p - refine_win)
        hi = min(len(x), p + refine_win + 1)
        local = np.abs(x[lo:hi])
        if local.size == 0:
            continue
        refined.append(lo + int(np.argmax(local)))
    refined = np.array(sorted(set(refined)), dtype=int)

    # Merge too-close peaks (keep the one with larger |x|)
    if refined.size > 1:
        keep = [refined[0]]
        for idx in refined[1:]:
            if idx - keep[-1] < refractory:
                keep[-1] = keep[-1] if abs(x[keep[-1]]) >= abs(x[idx]) else idx
            else:
                keep.append(idx)
        refined = np.array(keep, dtype=int)

    return refined


# ----------------------------------------------------------------------
# Core ST min-edge computation (shared by slope + plotting)
# ----------------------------------------------------------------------

def _st_minedge_core(
    sig: np.ndarray,
    fs: float,
    r_idx: int,
    use_st_filter: bool = True,
    prefiltered: np.ndarray | None = None,
    edge_len_ms: float = 20.0,
):
    """
    Internal helper that performs the min-of-edges ST slope computation
    and returns intermediate geometry for plotting.

    Detection region (updated):
      - ST window: [r_idx + 100 ms, r_idx + 160 ms]

    Returns:
        st_offset: float | None
        slope: float | None
        x_st: np.ndarray (signal used for ST, possibly filtered)
        baseline: float | None
        head_idx: int | None
        tail_idx: int | None
        st_win_start: int | None
        st_win_end: int | None
    """
    # Decide which signal to use for ST analysis
    if prefiltered is not None:
        x = prefiltered
    elif use_st_filter:
        x = filter_for_st(sig, fs)
    else:
        x = sig

    n = len(x)

    # PR baseline window
    pre_start = r_idx - int(0.20 * fs)  # -200 ms
    pre_end   = r_idx - int(0.12 * fs)  # -120 ms

    # ST window: [r + 100 ms, r + 160 ms]
    st_win_start = r_idx + int(0.10 * fs)  # +100 ms
    st_win_end   = r_idx + int(0.16 * fs)  # +160 ms

    if pre_start < 0 or st_win_end >= n:
        return None, None, x, None, None, None, None, None

    # Baseline from PR segment
    baseline = float(np.median(x[pre_start:pre_end]))

    # ST offset (for consistency): mean on [r+60 ms, r+80 ms]
    st_off_start = r_idx + int(0.06 * fs)  # +60 ms
    st_off_end   = r_idx + int(0.08 * fs)  # +80 ms
    if st_off_end >= n:
        return None, None, x, baseline, None, None, st_win_start, st_win_end
    st_offset = float(np.mean(x[st_off_start:st_off_end]) - baseline)

    if st_win_start >= st_win_end:
        return st_offset, None, x, baseline, None, None, st_win_start, st_win_end

    st_len = st_win_end - st_win_start

    # Number of samples at each edge (>=1, <= half window)
    edge_samples = int(edge_len_ms * 1e-3 * fs)
    edge_samples = max(1, edge_samples)
    edge_samples = min(edge_samples, st_len // 2)

    # Head and tail windows (indices)
    head_lo = st_win_start
    head_hi = st_win_start + edge_samples      # exclusive
    tail_lo = st_win_end - edge_samples
    tail_hi = st_win_end                       # exclusive

    # Baseline-removed values
    head_y = x[head_lo:head_hi] - baseline
    tail_y = x[tail_lo:tail_hi] - baseline

    if head_y.size == 0 or tail_y.size == 0:
        return st_offset, None, x, baseline, None, None, st_win_start, st_win_end

    # Take the minimum in each window as representative point
    head_idx_rel = int(np.argmin(head_y))
    tail_idx_rel = int(np.argmin(tail_y))

    head_idx = head_lo + head_idx_rel
    tail_idx = tail_lo + tail_idx_rel

    if tail_idx == head_idx:
        return st_offset, None, x, baseline, head_idx, tail_idx, st_win_start, st_win_end

    t1 = head_idx / fs
    t2 = tail_idx / fs
    y1 = head_y[head_idx_rel]
    y2 = tail_y[tail_idx_rel]

    slope = (y2 - y1) / (t2 - t1)  # mV/s

    return st_offset, float(slope), x, baseline, head_idx, tail_idx, st_win_start, st_win_end


# ----------------------------------------------------------------------
# Public: ST slope for a single beat (using min-of-edges method)
# ----------------------------------------------------------------------

def st_slope_for_beat(
    sig: np.ndarray,
    fs: float,
    r_idx: int,
    use_st_filter: bool = True,
    prefiltered: np.ndarray | None = None,
    edge_len_ms: float = 20.0,
):
    """
    Compute ST offset and slope for a single beat around an R-peak.

    Detection region:
      - ST analysis window: [r + 100 ms, r + 160 ms]
    """
    st_offset, slope, _, _, _, _, _, _ = _st_minedge_core(
        sig,
        fs,
        r_idx,
        use_st_filter=use_st_filter,
        prefiltered=prefiltered,
        edge_len_ms=edge_len_ms,
    )
    return st_offset, slope


def classify_slope(slope: float | None, thr: float = 0.5) -> str:
    """
    Convert numeric slope (mV/s) into a 3-class label: 'Up', 'Down', or 'Flat'.

      - |slope| <= thr -> 'Flat'
      - slope >  thr   -> 'Up'
      - slope < -thr   -> 'Down'
    """
    if slope is None:
        return "Flat"
    if slope > thr:
        return "Up"
    if slope < -thr:
        return "Down"
    return "Flat"


def st_slope_labels_for_signal(sig: np.ndarray, fs: float, thr: float = 0.5):
    """
    Convenience function:
      - Detect R-peaks on the raw signal.
      - Apply ST-segment filter (0.5–35 Hz) once on the whole signal.
      - Compute ST slope and label for each beat using the min-of-edges method.

    Returns:
        peaks:  1-D np.ndarray of R-peak indices
        slopes: list[float | None] of length len(peaks)
        labels: list[str] ('Up'/'Down'/'Flat') of length len(peaks)
    """
    peaks = robust_r_peaks(sig, fs)
    sig_st = filter_for_st(sig, fs)

    slopes = []
    labels = []
    for r in peaks:
        _, k = st_slope_for_beat(
            sig,
            fs,
            r,
            use_st_filter=False,   # we pass prefiltered
            prefiltered=sig_st,
        )
        slopes.append(k)
        labels.append(classify_slope(k, thr=thr))

    return peaks, slopes, labels


# ----------------------------------------------------------------------
# Plotting helper: mark detection region and min-edge points
# ----------------------------------------------------------------------

def plot_st_slope_beat(
    sig: np.ndarray,
    fs: float,
    r_idx: int,
    slope: float | None,
    pred_label: str,
    true_label: str | None,
    out_dir: str,
    rec_name: str = "unknownrec",
    ch: int | None = None,
    beat_idx: int | None = None,
    window_ms_before: float = 300.0,
    window_ms_after: float = 400.0,
    edge_len_ms: float = 20.0,
):
    """
    Plot a single beat around an R-peak, highlight the ST detection region
    [r + 100 ms, r + 160 ms], and mark the two min-edge representative points.

    The figure is saved to `out_dir` as a PNG.

    Args:
        sig: full ECG signal (in mV, or same unit consistently).
        fs: sampling frequency in Hz.
        r_idx: index of the R-peak for this beat.
        slope: ST slope (mV/s), can be None.
        pred_label: predicted ST label ('Up'/'Down'/'Flat').
        true_label: ground-truth ST label ('Up'/'Down') or None.
        out_dir: folder where the PNG will be stored.
        rec_name: optional record name (for filename and title).
        ch: optional channel index (for filename and title).
        beat_idx: optional beat index (for filename).
        window_ms_before: time window (ms) before R to show.
        window_ms_after: time window (ms) after R to show.
        edge_len_ms: edge length (ms) used for min-of-edges.
    """
    os.makedirs(out_dir, exist_ok=True)

    # Use ST-filtered signal for visualization
    sig_st = filter_for_st(sig, fs)

    # Re-run core to get baseline and geometry
    st_offset, slope_core, x_st, baseline, head_idx, tail_idx, st_win_start, st_win_end = _st_minedge_core(
        sig,
        fs,
        r_idx,
        use_st_filter=False,
        prefiltered=sig_st,
        edge_len_ms=edge_len_ms,
    )

    # If caller passed slope=None, use the core result
    if slope is None:
        slope = slope_core

    # Time axis (full signal)
    n = len(sig_st)
    t = np.arange(n) / fs

    # Plot window around R
    win_before = int(window_ms_before * 1e-3 * fs)
    win_after = int(window_ms_after * 1e-3 * fs)
    lo = max(0, r_idx - win_before)
    hi = min(n, r_idx + win_after)

    t_win = t[lo:hi]
    y_win = sig_st[lo:hi]

    # Figure
    plt.figure(figsize=(8, 4))
    plt.plot(t_win, y_win, label="ST-filtered ECG")

    # R-peak marker (if in range)
    if lo <= r_idx < hi:
        plt.axvline(t[r_idx], linestyle="--", linewidth=1.0, label="R-peak")

    # Highlight ST detection region [r+100ms, r+160ms] if inside window
    if st_win_start is not None and st_win_end is not None:
        st_lo_t = t[st_win_start]
        st_hi_t = t[st_win_end - 1]
        plt.axvspan(st_lo_t, st_hi_t, alpha=0.2, label="ST detection region")

    # Plot baseline as a horizontal line (if available)
    if baseline is not None:
        plt.axhline(baseline, linestyle=":", linewidth=1.0, label="Baseline (PR)")

    # Mark min-edge points
    if head_idx is not None and tail_idx is not None:
        plt.plot(
            t[head_idx],
            x_st[head_idx],
            marker="o",
            markersize=6,
            label="Head min",
        )
        plt.plot(
            t[tail_idx],
            x_st[tail_idx],
            marker="o",
            markersize=6,
            label="Tail min",
        )

        # Line whose slope we use
        plt.plot(
            [t[head_idx], t[tail_idx]],
            [x_st[head_idx], x_st[tail_idx]],
            linestyle="--",
            linewidth=1.0,
            label="Slope line",
        )

    # Title with slope, true and predicted labels
    ch_str = f", ch{ch}" if ch is not None else ""
    beat_str = f", beat{beat_idx}" if beat_idx is not None else ""
    if slope is not None:
        if true_label is not None:
            title = (
                f"{rec_name}{ch_str}{beat_str} | "
                f"true={true_label}, pred={pred_label}, slope={slope:.2f} mV/s"
            )
        else:
            title = (
                f"{rec_name}{ch_str}{beat_str} | "
                f"pred={pred_label}, slope={slope:.2f} mV/s"
            )
    else:
        if true_label is not None:
            title = (
                f"{rec_name}{ch_str}{beat_str} | "
                f"true={true_label}, pred={pred_label}, slope=None"
            )
        else:
            title = (
                f"{rec_name}{ch_str}{beat_str} | "
                f"pred={pred_label}, slope=None"
            )

    plt.title(title)
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.legend(loc="best")
    plt.tight_layout()

    # Filename: include true and pred
    true_str = true_label if true_label is not None else "None"
    fname_parts = [rec_name]
    if ch is not None:
        fname_parts.append(f"ch{ch}")
    if beat_idx is not None:
        fname_parts.append(f"beat{beat_idx}")
    fname_parts.append(f"true-{true_str}")
    fname_parts.append(f"pred-{pred_label}")
    fname = "_".join(fname_parts) + ".png"

    out_path = os.path.join(out_dir, fname)
    plt.savefig(out_path, dpi=150)
    plt.close()
