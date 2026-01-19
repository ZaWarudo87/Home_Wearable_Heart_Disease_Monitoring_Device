import os
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt


def robust_r_peaks(sig_mV: np.ndarray, fs: float) -> np.ndarray:
    """
    Pan-Tompkins style R-peak detection with adaptive thresholds.

    This is a standalone version of the method you use in main.py:
    - 2nd-order 5–20 Hz band-pass
    - derivative -> square -> moving window integration (~150 ms)
    - robust z-score thresholding on the integrated signal
    - peak refinement on the band-passed signal
    """
    # 1) Bandpass to enhance QRS (wider band, keep morphology)
    b, a = signal.butter(2, [5 / (fs / 2), 20 / (fs / 2)], btype="bandpass")
    x = signal.filtfilt(b, a, sig_mV)

    # 2) Derivative -> Square -> Moving Window Integration (~150 ms)
    dx = np.diff(x, prepend=x[0])
    sq = dx * dx
    win = max(1, int(0.15 * fs))
    mwi = np.convolve(sq, np.ones(win) / win, mode="same")

    # 3) Robust normalization & adaptive thresholds (z-score via MAD)
    med = np.median(mwi)
    mad = np.median(np.abs(mwi - med)) + 1e-12
    z = (mwi - med) / mad

    refractory = int(0.28 * fs)  # 280 ms
    height = 3.0                  # z units
    prom = 1.5                    # z units

    peaks_mwi, _ = signal.find_peaks(
        z,
        distance=refractory,
        height=height,
        prominence=prom,
    )

    if peaks_mwi.size == 0:
        return peaks_mwi

    # 4) Refine peaks on band-passed signal (±80 ms)
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

    # 5) Merge peaks that are too close (keep the stronger one in |x|)
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
# Core ST computation helper (for slope + plotting)
# ----------------------------------------------------------------------

def _st_core_for_beat(sig: np.ndarray, fs: float, r_idx: int):
    """
    Internal helper that performs the baseline ST-slope computation and
    returns extra geometry for plotting.

    Windows (baseline version):
      - Baseline (PR segment):   [r - 200 ms, r - 120 ms]
      - ST window for slope:     [r + 100 ms, r + 160 ms]

    Returns:
        st_offset: float | None
        slope: float | None
        baseline: float | None
        pre_start: int | None
        pre_end: int | None
        st_start: int | None
        st_end: int | None
    """
    pre_start = r_idx - int(0.20 * fs)  # -200 ms
    pre_end = r_idx - int(0.12 * fs)    # -120 ms
    st_start = r_idx + int(0.10 * fs)   # +100 ms
    st_end = r_idx + int(0.16 * fs)     # +160 ms

    n = len(sig)
    if pre_start < 0 or st_end >= n:
        return None, None, None, None, None, None, None

    baseline = float(np.median(sig[pre_start:pre_end]))

    # ST offset: mean ST segment - baseline
    st_offset = float(np.mean(sig[st_start:st_end]) - baseline)

    # ST slope: linear regression on baseline-referenced segment
    x = np.arange(st_start, st_end) / fs
    y = sig[st_start:st_end] - baseline
    if x.size < 3:
        return st_offset, None, baseline, pre_start, pre_end, st_start, st_end

    k, _ = np.polyfit(x, y, 1)  # mV/s

    return st_offset, float(k), baseline, pre_start, pre_end, st_start, st_end


def st_slope_for_beat(sig: np.ndarray, fs: float, r_idx: int):
    """
    Compute ST offset and slope for a single beat around an R-peak.

    Windows are aligned with your compute_ecg_features() implementation:
      - Baseline (PR segment):   [r - 200 ms, r - 120 ms]
      - ST window for slope:     [r + 100 ms, r + 160 ms]

    Returns:
        (st_offset, st_slope) in mV and mV/s.
        If windows go out of range or too short, returns (None, None).
    """
    st_offset, slope, _, _, _, _, _ = _st_core_for_beat(sig, fs, r_idx)
    return st_offset, slope


def classify_slope(slope: float | None, thr: float = 0.0) -> str:
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


def st_slope_labels_for_signal(sig: np.ndarray, fs: float, thr: float = 0.0):
    """
    Convenience function:
      - Detect R-peaks on the whole signal.
      - Compute ST slope and label for each beat.

    Returns:
        peaks: 1-D np.ndarray of R-peak indices
        slopes: list[float | None] of length len(peaks)
        labels: list[str] ('Up'/'Down'/'Flat') of length len(peaks)
    """
    peaks = robust_r_peaks(sig, fs)
    slopes = []
    labels = []
    for r in peaks:
        _, k = st_slope_for_beat(sig, fs, r)
        slopes.append(k)
        labels.append(classify_slope(k, thr=thr))
    return peaks, slopes, labels


# ----------------------------------------------------------------------
# Plotting helper: mark ST window, baseline, and slope line
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
    lead_name: str | None = None,
):
    """
    Plot a single beat around an R-peak, highlight the ST detection region
    [r + 100 ms, r + 160 ms], and show the regression line used for slope.

    The figure is saved to `out_dir` as a PNG.

    Args:
        sig: full ECG signal (in mV, or same unit consistently).
        fs: sampling frequency in Hz.
        r_idx: index of the R-peak for this beat.
        slope: ST slope (mV/s), can be None (we recompute if needed).
        pred_label: predicted ST label ('Up'/'Down'/'Flat').
        true_label: ground-truth ST label ('Up'/'Down') or None.
        out_dir: folder where the PNG will be stored.
        rec_name: optional record name (for filename and title).
        ch: optional channel index (kept only for uniqueness in filename).
        beat_idx: optional beat index (for filename).
        window_ms_before: time window (ms) before R to show.
        window_ms_after: time window (ms) after R to show.
        lead_name: optional lead name (e.g. 'MLIII'), shown in title and filename.
    """
    os.makedirs(out_dir, exist_ok=True)

    # Re-run core to get baseline and geometry
    st_offset, slope_core, baseline, pre_start, pre_end, st_start, st_end = _st_core_for_beat(
        sig, fs, r_idx
    )

    # If caller passed slope=None, use the core result
    if slope is None:
        slope = slope_core

    n = len(sig)
    t = np.arange(n) / fs

    # Plot window around R
    win_before = int(window_ms_before * 1e-3 * fs)
    win_after = int(window_ms_after * 1e-3 * fs)
    lo = max(0, r_idx - win_before)
    hi = min(n, r_idx + win_after)

    t_win = t[lo:hi]
    y_win = sig[lo:hi]

    plt.figure(figsize=(8, 4))
    plt.plot(t_win, y_win, label="ECG (raw)")

    # Mark R-peak
    if lo <= r_idx < hi:
        plt.axvline(t[r_idx], linestyle="--", linewidth=1.0, label="R-peak")

    # Mark PR baseline window
    if pre_start is not None and pre_end is not None:
        if lo <= pre_start < hi or lo < pre_end <= hi:
            pr_lo_t = t[pre_start]
            pr_hi_t = t[pre_end - 1]
            plt.axvspan(pr_lo_t, pr_hi_t, alpha=0.2, label="PR baseline window")

    # Mark ST detection window [r+100 ms, r+160 ms]
    if st_start is not None and st_end is not None:
        if lo <= st_start < hi or lo < st_end <= hi:
            st_lo_t = t[st_start]
            st_hi_t = t[st_end - 1]
            plt.axvspan(st_lo_t, st_hi_t, alpha=0.2, label="ST window (100-160 ms)")

    # Baseline as a horizontal line
    if baseline is not None:
        plt.axhline(baseline, linestyle=":", linewidth=1.0, label="Baseline (PR)")

    # Plot regression line used for slope
    if baseline is not None and st_start is not None and st_end is not None and slope is not None:
        x = np.arange(st_start, st_end) / fs
        y = sig[st_start:st_end] - baseline
        if x.size >= 2:
            # recompute intercept for plotting (slope should match st_slope_for_beat)
            k, b = np.polyfit(x, y, 1)
            y_fit = k * x + b + baseline
            plt.plot(x, y_fit, linestyle="--", linewidth=1.0, label="ST slope line")

    # Lead/beat info for title
    lead_str = f", lead={lead_name}" if lead_name is not None else ""
    beat_str = f", beat{beat_idx}" if beat_idx is not None else ""
    if slope is not None:
        if true_label is not None:
            title = (
                f"{rec_name}{lead_str}{beat_str} | "
                f"true={true_label}, pred={pred_label}, slope={slope:.2f} mV/s"
            )
        else:
            title = (
                f"{rec_name}{lead_str}{beat_str} | "
                f"pred={pred_label}, slope={slope:.2f} mV/s"
            )
    else:
        if true_label is not None:
            title = (
                f"{rec_name}{lead_str}{beat_str} | "
                f"true={true_label}, pred={pred_label}, slope=None"
            )
        else:
            title = (
                f"{rec_name}{lead_str}{beat_str} | "
                f"pred={pred_label}, slope=None"
            )

    plt.title(title)
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.legend(loc="best")
    plt.tight_layout()

    # Filename: include lead, true, pred
    true_str = true_label if true_label is not None else "None"
    fname_parts = [rec_name]
    if lead_name is not None:
        fname_parts.append(f"lead-{lead_name}")
    elif ch is not None:
        fname_parts.append(f"ch{ch}")
    if beat_idx is not None:
        fname_parts.append(f"beat{beat_idx}")
    fname_parts.append(f"true-{true_str}")
    fname_parts.append(f"pred-{pred_label}")
    fname = "_".join(fname_parts) + ".png"

    out_path = os.path.join(out_dir, fname)
    plt.savefig(out_path, dpi=150)
    plt.close()
