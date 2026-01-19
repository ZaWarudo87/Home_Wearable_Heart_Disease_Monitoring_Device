import numpy as np
from scipy import signal


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


def st_slope_for_beat(sig: np.ndarray, fs: float, r_idx: int):
    """
    Compute ST offset and slope for a single beat around an R-peak.

    Windows are aligned with your compute_ecg_features() implementation:
      - Baseline (PR segment):   [r - 200 ms, r - 120 ms]
      - J point:                 r + 40 ms
      - ST offset window:        [r + 60 ms, r + 80 ms]
      - ST slope: linear fit on  [J, J + 80 ms] after baseline removal

    Returns:
        (st_offset, st_slope) in mV and mV/s.
        If windows go out of range or too short, returns (None, None).
    """
    pre_start = r_idx - int(0.20 * fs)
    pre_end = r_idx - int(0.12 * fs)
    j = r_idx + int(0.04 * fs)
    st_start = r_idx + int(0.10 * fs)
    st_end = r_idx + int(0.16 * fs)

    n = len(sig)
    if pre_start < 0 or st_end >= n:
        return None, None

    baseline = float(np.median(sig[pre_start:pre_end]))

    # ST offset: mean ST segment - baseline
    st_offset = float(np.mean(sig[st_start:st_end]) - baseline)

    # ST slope: linear regression on baseline-referenced segment (J -> J+80 ms)
    x = np.arange(st_start, st_end) / fs
    y = sig[st_start:st_end] - baseline
    if x.size < 3:
        return st_offset, None

    k, _ = np.polyfit(x, y, 1)  # mV/s
    return st_offset, float(k)


def classify_slope(slope: float | None, thr: float = 0.0) -> str:
    """
    Convert numeric slope (mV/s) into a 3-class label: 'Up', 'Down', or 'Flat'.

    Same logic as your compute_ecg_features():
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
