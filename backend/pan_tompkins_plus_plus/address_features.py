# -*- coding: utf-8 -*-
from pathlib import Path
import glob
import numpy as np
import time
import csv
from scipy import signal

try:
    from .algos.pan_tompkins_plus_plus import Pan_Tompkins_Plus_Plus as RpeakDetection
except:
    from algos.pan_tompkins_plus_plus import Pan_Tompkins_Plus_Plus as RpeakDetection

# Function that computes ECG features for a given signal segment
def compute_ecg_features(sig, fs, use_st_filter=True, detector=None):
    sig = np.asarray(sig, dtype=float)
    n = sig.size

    if use_st_filter:
        sig = filter_for_st(sig, fs)

    # R-peak detection
    det = detector or RpeakDetection()
    peaks = np.asarray(det.rpeak_detection(sig, fs), dtype=int)

    # Enforce max HR by refractory period
    HR_MAX = 200.0
    min_rr_sec = 60.0 / HR_MAX
    refractory = int(round(min_rr_sec * fs))
    if peaks.size:
        keep = [peaks[0]]
        for k in range(1, len(peaks)):
            if peaks[k] - keep[-1] >= refractory:
                keep.append(peaks[k])
        peaks = np.asarray(keep, dtype=int)
    beats_count = int(peaks.size)

    if beats_count >= 2:
        rr = np.diff(peaks) / float(fs)
        hr_inst = 60.0 / rr
        hr_valid = hr_inst[hr_inst <= HR_MAX]
        if hr_valid.size:
            max_hr = float(np.max(hr_valid))
            avg_hr = float(np.mean(hr_valid))
        else:
            max_hr = np.nan
            avg_hr = np.nan
    else:
        max_hr = np.nan
        avg_hr = np.nan

    # ST segment features (baseline-referenced)
    st_vals, slopes = [], []
    pre_w1 = int(0.20 * fs)
    pre_w2 = int(0.12 * fs)
    j_off = int(0.04 * fs)
    st_s = int(0.10 * fs)
    st_e = int(0.16 * fs)
    slope_win = int(0.06 * fs)

    for r in peaks:
        pre_start = r - pre_w1
        pre_end = r - pre_w2
        j = r + j_off
        st_start = r + st_s
        st_end = r + st_e

        if pre_start < 0 or pre_end <= pre_start or st_end >= n or j >= n:
            continue

        baseline = float(np.median(sig[pre_start:pre_end]))

        st_seg = sig[st_start:st_end] - baseline
        if st_seg.size:
            st_vals.append(float(np.mean(st_seg)))

        j_end = min(j + slope_win, n)
        x = np.arange(j, j_end) / float(fs)
        y = sig[j:j_end] - baseline
        if x.size >= 3:
            k, _ = np.polyfit(x, y, 1)
            slopes.append(float(k))

    st_median = float(np.median(st_vals)) if st_vals else np.nan
    st_slope = float(np.median(slopes)) if slopes else np.nan

    thr_slope = 0.5  # mV/s
    if np.isfinite(st_slope):
        if st_slope > thr_slope:
            st_label = "Up"
        elif st_slope < -thr_slope:
            st_label = "Down"
        else:
            st_label = "Flat"
    else:
        st_label = None

    # Map to model-ready feature names
    return {
        "Max_HR": max_hr,
        "Avg_HR": avg_hr,
        "Oldpeak": st_median,
        "RestingECG": "ST" if (np.isfinite(st_median) and abs(st_median) > 0.05) else "Normal",
        "ST_Slope": st_slope,
        "ST_Label": st_label,
        "n_beats": beats_count,
    }

# ST-focused bandpass: 0.5-35 Hz

def filter_for_st(sig: np.ndarray, fs: float) -> np.ndarray:
    sig = np.asarray(sig, dtype=float)
    
    # High-pass filter (3rd-order Butterworth), cutoff = 0.5 Hz
    hp_cut = 0.5
    hp_N = 3
    Wn_hp = hp_cut * 2.0 / fs

    bhp, ahp = signal.butter(hp_N, Wn_hp, btype="highpass")
    sig_hp = signal.filtfilt(bhp, ahp, sig)

    # Low-pass filter (3rd-order Butterworth), cutoff = 35 Hz
    lp_cut = 35.0
    lp_N = 3
    Wn_lp = lp_cut * 2.0 / fs

    blp, alp = signal.butter(lp_N, Wn_lp, btype="lowpass")
    sig_bp = signal.filtfilt(blp, alp, sig_hp)

    return sig_bp

# ===== Tunables =====
FS_sample = 160.0
TIMESTAMP_COL = "timestamp"
VALUE_COL = "ecg_value"

def read_csv_one(path):
    ts, val = [], []
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts.append(float(row[TIMESTAMP_COL]))
                val.append(float(row[VALUE_COL]))
            except Exception:
                continue
    ts = np.asarray(ts, float)
    val = np.asarray(val, float)
    if ts.size < 3:
        raise ValueError(f"{path} too short to estimate sampling rate")
    return ts, val

# ===== Main execution =====
det = RpeakDetection()

# ts unused
def calc_features(ts: np.ndarray, ecg: np.ndarray, i: int = 0, base: str = "rest_ecg_data_", debug: bool = False) -> dict:
    st_time = time.time()
    fs_i = int(round(FS_sample))
    qrs = np.asarray(det.rpeak_detection(ecg, fs_i), dtype=int)

    if qrs.size:
        refractory = int(round(0.200 * fs_i))
        keep = [qrs[0]]
        for k in range(1, len(qrs)):
            if qrs[k] - keep[-1] >= refractory:
                keep.append(qrs[k])
        qrs = np.asarray(keep, dtype=int)

    if debug:
        print(
            f"[{i}/{len(files)}] {base:>20s}  "
            f"| peaks={len(qrs)}"
        )

    # features = compute_ecg_features(ecg_use, fs_i, use_st_filter=False)
    features_stfilt = compute_ecg_features(ecg, fs_i, use_st_filter=True)

    if debug:
        print("result :")
        print(
            f"  MAX HR={features_stfilt['Max_HR']:.1f} bpm, "
            f"ST_label={features_stfilt['ST_Label']}, "
            f"Oldpeak={features_stfilt['Oldpeak']:.3f} mV"
        )

    feature_out = {
        "file": base,
        "fs_hz": round(FS_sample, 2),
        "max_hr": round(features_stfilt["Max_HR"], 1),
        "avg_hr": round(features_stfilt["Avg_HR"], 1),
        "st_label": features_stfilt["ST_Label"],
        "oldpeak": round(features_stfilt["Oldpeak"], 3),
        "resting_ecg": features_stfilt["RestingECG"],
        "calc_time": time.time() - st_time
    }
    return feature_out

if __name__ == "__main__":
    PROJ_DIR = Path(__file__).resolve().parent
    CSV_DIR = PROJ_DIR.parent.parent / "ESP32" / "ECG_DATA"

    if not CSV_DIR.exists():
        raise FileNotFoundError(f"Missing ECG_DATA folder: {CSV_DIR}")

    # Read all CSVs under ECG_DATA
    files = sorted(glob.glob(str(CSV_DIR / "*.csv")))
    if not files:
        raise FileNotFoundError(f"No CSV files found: {CSV_DIR}/*.csv")


    print(f"[INFO] CSV dir: {CSV_DIR}")
    print(f"[INFO] Found {len(files)} CSVs:")

    # Output folder for window-level features
    out_dir = PROJ_DIR / "results_csv"
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, csv_path in enumerate(files, 1):
        base = Path(csv_path).stem

        ts, ecg = read_csv_one(csv_path)
        feature_out = calc_features(ts, ecg, i, base, True)

        feature_csv = out_dir / "window_features.csv"
        write_header = not feature_csv.exists()

        with open(feature_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=feature_out.keys())
            if write_header:
                writer.writeheader()
            writer.writerow(feature_out)

