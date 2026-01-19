# st_slope_detector_minedge.py
import numpy as np
from scipy import signal


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
# ST slope for a single beat: min-of-edges method
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
    Compute ST slope using a "min-of-edges" method on the ST segment.

    Windows (aligned with your original implementation):
      - Baseline (PR segment):   [r - 200 ms, r - 120 ms]
      - J point:                 r + 40 ms
      - ST analysis window:      [J, J + 80 ms]  (80 ms total)

    New slope definition:
      - Let N_edge be the number of samples corresponding to `edge_len_ms`.
      - On the ST window [J, J+80 ms], we take:
          head_window  = first N_edge samples
          tail_window  = last  N_edge samples
      - In each window, we pick the minimum value (baseline-removed) as
        the representative point.
      - ST slope = (y_tail - y_head) / (t_tail - t_head) in mV/s.

    Filtering behavior:
      - If `prefiltered` is provided -> use it directly.
      - Else if `use_st_filter` is True -> filter_for_st(sig, fs) is applied.
      - Else -> use raw `sig`.

    Returns:
        (st_offset, st_slope) in mV and mV/s.
        If windows go out of range or too short, returns (None, None).
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

    # J point and ST window (80 ms)
    j       = r_idx + int(0.04 * fs)    # +40 ms
    st_end  = j + int(0.08 * fs)        # J + 80 ms

    if pre_start < 0 or st_end >= n:
        return None, None

    # Baseline from PR segment
    baseline = float(np.median(x[pre_start:pre_end]))

    # ST offset (optional): mean on [r+60 ms, r+80 ms] as before
    st_off_start = r_idx + int(0.06 * fs)  # +60 ms
    st_off_end   = r_idx + int(0.08 * fs)  # +80 ms
    if st_off_end >= n:
        return None, None
    st_offset = float(np.mean(x[st_off_start:st_off_end]) - baseline)

    # ----- Min-of-edges slope on [J, J+80 ms] -----
    st_win_start = j
    st_win_end   = st_end  # exclusive index

    if st_win_start >= st_win_end:
        return st_offset, None

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
        return st_offset, None

    # Take the minimum in each window as representative point
    head_idx_rel = int(np.argmin(head_y))
    tail_idx_rel = int(np.argmin(tail_y))

    head_idx = head_lo + head_idx_rel
    tail_idx = tail_lo + tail_idx_rel

    if tail_idx == head_idx:
        return st_offset, None

    t1 = head_idx / fs
    t2 = tail_idx / fs
    y1 = head_y[head_idx_rel]
    y2 = tail_y[tail_idx_rel]

    slope = (y2 - y1) / (t2 - t1)  # mV/s

    return st_offset, float(slope)


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
