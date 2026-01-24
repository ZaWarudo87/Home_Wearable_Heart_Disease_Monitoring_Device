# -*- coding: utf-8 -*-
from pathlib import Path
import glob
import numpy as np
import time
import csv
from scipy import signal

from algos.pan_tompkins_plus_plus import Pan_Tompkins_Plus_Plus as RpeakDetection

def compute_ecg_features(sig, fs, use_st_filter=True):
    sig = np.asarray(sig, dtype=float)
    n = sig.size

    if use_st_filter:
        sig = filter_for_st(sig, fs)

    peaks = np.asarray(RpeakDetection().rpeak_detection(sig, fs), dtype=int)

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
        else:
            max_hr = np.nan
    else:
        max_hr = np.nan

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

    return {
        "HR": max_hr,
        "Oldpeak": st_median,
        "RestingECG": "ST" if (np.isfinite(st_median) and abs(st_median) > 0.05) else "Normal",
        "ST_Slope": st_slope,
        "ST_Label": st_label,
        "n_beats": beats_count,
    }

def filter_for_st(sig, fs):
    sig = np.asarray(sig, dtype=float)

    hp_cut = 0.5
    hp_N = 3
    Wn_hp = hp_cut * 2.0 / fs
    bhp, ahp = signal.butter(hp_N, Wn_hp, btype="highpass")
    sig_hp = signal.filtfilt(bhp, ahp, sig)

    lp_cut = 35.0
    lp_N = 3
    Wn_lp = lp_cut * 2.0 / fs
    blp, alp = signal.butter(lp_N, Wn_lp, btype="lowpass")
    sig_bp = signal.filtfilt(blp, alp, sig_hp)

    return sig_bp

# ===== Tunables =====
DRAW_EVERY = 1
MAX_FILES = None
RESAMPLE_TO = None
TIMESTAMP_COL = "timestamp"
VALUE_COL = "ecg_value"

def read_csv_one(path):
    ts, val = [], []
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = [h.strip() for h in reader.fieldnames] if reader.fieldnames else []
        name_map = {h.strip(): h for h in reader.fieldnames} if reader.fieldnames else {}
        if TIMESTAMP_COL not in fields or VALUE_COL not in fields:
            raise ValueError(
                f"{path} missing required columns {TIMESTAMP_COL},{VALUE_COL} (header={reader.fieldnames})"
            )
        for row in reader:
            try:
                ts.append(float(row[name_map[TIMESTAMP_COL]].strip()))
                val.append(float(row[name_map[VALUE_COL]].strip()))
            except Exception:
                continue
    ts = np.asarray(ts, dtype=float)
    val = np.asarray(val, dtype=float)
    if ts.size < 3:
        raise ValueError(f"{path} too short to estimate sampling rate")
    return ts, val

def estimate_fs(timestamps):
    dt = np.diff(timestamps)
    dt = dt[(dt > 0) & np.isfinite(dt)]
    if dt.size == 0:
        raise ValueError("timestamp cannot estimate dt")
    fs = 1.0 / np.median(dt)
    stats = dict(
        dt_ms_mean=np.mean(dt) * 1000.0,
        dt_ms_std=np.std(dt) * 1000.0,
        dt_ms_min=np.min(dt) * 1000.0,
        dt_ms_max=np.max(dt) * 1000.0,
    )
    return float(fs), stats

def linear_resample(ts, x, fs_target):
    t0, t1 = ts[0], ts[-1]
    n = int(np.floor((t1 - t0) * fs_target)) + 1
    if n <= 1:
        return x.copy(), fs_target, ts.copy()
    t_new = t0 + np.arange(n) / fs_target
    x_new = np.interp(t_new, ts, x)
    return x_new, fs_target, t_new

# ===== Main execution =====
det = RpeakDetection()

def calc_features(ts: np.ndarray, ecg: np.ndarray, i: int = 0, base: str = "-") -> None:
    fs_est, dt_stats = estimate_fs(ts)

    if RESAMPLE_TO is not None and RESAMPLE_TO > 0:
        ecg_use, fs_float, ts_rs = linear_resample(ts, ecg, float(RESAMPLE_TO))
    else:
        ecg_use, fs_float, ts_rs = ecg, fs_est, ts

    fs_i = int(round(fs_float))
    qrs = np.asarray(det.rpeak_detection(ecg_use, fs_i), dtype=int)

    if qrs.size:
        refractory = int(round(0.200 * fs_i))
        keep = [qrs[0]]
        for k in range(1, len(qrs)):
            if qrs[k] - keep[-1] >= refractory:
                keep.append(qrs[k])
        qrs = np.asarray(keep, dtype=int)

    print(
        f"[{i}/{len(files)}] {base:>20s} | fs≈{fs_est:.2f} Hz "
        f"(dt_mean={dt_stats['dt_ms_mean']:.3f} ms, std={dt_stats['dt_ms_std']:.3f} ms) "
        f"| peaks={len(qrs)}"
    )

    features = compute_ecg_features(ecg_use, fs_i, use_st_filter=False)
    features_stfilt = compute_ecg_features(ecg_use, fs_i, use_st_filter=True)

    print("result :")
    print(
        f"  MAX HR={features['HR']:.1f} bpm, "
        f"ST_label={features_stfilt['ST_Label']}, "
        f"Oldpeak={features_stfilt['Oldpeak']:.3f} mV"
    )

    feature_out = {
        "file": base,
        "fs_hz": round(fs_est, 2),
        "max_hr": round(features["HR"], 1),
        "st_label": features_stfilt["ST_Label"],
        "oldpeak": round(features_stfilt["Oldpeak"], 3),
        "resting_ecg": features_stfilt["RestingECG"],
    }

if __name__ == "__main__":
    PROJ_DIR = Path(__file__).resolve().parent
    CSV_DIR = PROJ_DIR / "ECG_DATA"

    if not CSV_DIR.exists():
        raise FileNotFoundError(f"Missing ECG_DATA folder: {CSV_DIR}")

    files = sorted(glob.glob(str(CSV_DIR / "*.csv")))
    if not files:
        raise FileNotFoundError(f"No CSV files found: {CSV_DIR}/*.csv")

    if MAX_FILES:
        files = files[:MAX_FILES]

    print(f"[INFO] CSV dir: {CSV_DIR}")
    print(f"[INFO] Found {len(files)} CSVs:", [Path(f).name for f in files][:5], "..." if len(files) > 5 else "")

    out_dir = PROJ_DIR / "results_csv"
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    for i, csv_path in enumerate(files, 1):
        base = Path(csv_path).stem

        ts, ecg = read_csv_one(csv_path)
        fs_est, dt_stats = estimate_fs(ts)

        if RESAMPLE_TO is not None and RESAMPLE_TO > 0:
            ecg_use, fs_float, ts_rs = linear_resample(ts, ecg, float(RESAMPLE_TO))
        else:
            ecg_use, fs_float, ts_rs = ecg, fs_est, ts

        fs_i = int(round(fs_float))
        qrs = np.asarray(det.rpeak_detection(ecg_use, fs_i), dtype=int)

        if qrs.size:
            refractory = int(round(0.200 * fs_i))
            keep = [qrs[0]]
            for k in range(1, len(qrs)):
                if qrs[k] - keep[-1] >= refractory:
                    keep.append(qrs[k])
            qrs = np.asarray(keep, dtype=int)

        print(
            f"[{i}/{len(files)}] {base:>20s} | fs≈{fs_est:.2f} Hz "
            f"(dt_mean={dt_stats['dt_ms_mean']:.3f} ms, std={dt_stats['dt_ms_std']:.3f} ms) "
            f"| peaks={len(qrs)}"
        )

        features = compute_ecg_features(ecg_use, fs_i, use_st_filter=False)
        features_stfilt = compute_ecg_features(ecg_use, fs_i, use_st_filter=True)

        print("result :")
        print(
            f"  MAX HR={features['HR']:.1f} bpm, "
            f"ST_label={features_stfilt['ST_Label']}, "
            f"Oldpeak={features_stfilt['Oldpeak']:.3f} mV"
        )

        feature_out = {
            "file": base,
            "fs_hz": round(fs_est, 2),
            "max_hr": round(features["HR"], 1),
            "st_label": features_stfilt["ST_Label"],
            "oldpeak": round(features_stfilt["Oldpeak"], 3),
            "resting_ecg": features_stfilt["RestingECG"],
        }

        feature_csv = out_dir / "window_features.csv"
        write_header = not feature_csv.exists()

        with open(feature_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=feature_out.keys())
            if write_header:
                writer.writeheader()
            writer.writerow(feature_out)
