# -*- coding: utf-8 -*-
import csv
import glob
from pathlib import Path

import numpy as np
import pandas as pd

from algos.pan_tompkins_plus_plus import Pan_Tompkins_Plus_Plus as RpeakDetection

TIMESTAMP_COL = "timestamp"
VALUE_COL     = "ecg_value"


def read_csv_one(path):
    ts, val = [], []
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV has no header")

        fields = [h.strip() for h in reader.fieldnames]
        name_map = {h.strip(): h for h in reader.fieldnames}

        if TIMESTAMP_COL not in fields or VALUE_COL not in fields:
            raise ValueError("Missing required columns")

        for row in reader:
            try:
                ts.append(float(row[name_map[TIMESTAMP_COL]]))
                val.append(float(row[name_map[VALUE_COL]]))
            except Exception:
                continue

    ts = np.asarray(ts)
    val = np.asarray(val)
    if len(ts) < 3:
        raise ValueError("Too short")
    return ts, val


def estimate_fs(ts):
    dt = np.diff(ts)
    dt = dt[(dt > 0) & np.isfinite(dt)]
    fs = 1.0 / np.median(dt)
    return fs


def main():
    det = RpeakDetection()

    proj_dir = Path(__file__).resolve().parent
    csv_dir  = proj_dir / "ECG_DATA"

    files = sorted(glob.glob(str(csv_dir / "*.csv")))
    if not files:
        raise FileNotFoundError("No CSV files found")

    rows = []

    for idx, csv_path in enumerate(files, 1):
        base = Path(csv_path).stem

        try:
            ts, ecg = read_csv_one(csv_path)
            fs_est = estimate_fs(ts)
            fs_i = int(round(fs_est))

            # R-peak detection
            qrs = np.asarray(det.rpeak_detection(ecg, fs_i), dtype=int)

            # 200 ms refractory
            if qrs.size:
                refractory = int(round(0.200 * fs_i))
                keep = [qrs[0]]
                for k in range(1, len(qrs)):
                    if qrs[k] - keep[-1] >= refractory:
                        keep.append(qrs[k])
                qrs = np.asarray(keep)

            # features
            features = det.compute_ecg_features(ecg, fs_i)
            features_st = det.compute_ecg_features_stfilt(ecg, fs_i)

            rows.append({
                "file": base,
                "fs_hz": round(fs_est, 2),
                "n_peaks": int(len(qrs)),
                "max_hr_bpm": round(features["HR"], 1),
                "st_label": features_st["ST_Label"],
                "oldpeak_mV": round(features_st["Oldpeak"], 3),
            })

            print(f"[{idx}/{len(files)}] {base} OK")

        except Exception as e:
            rows.append({
                "file": base,
                "fs_hz": np.nan,
                "n_peaks": np.nan,
                "max_hr_bpm": np.nan,
                "st_label": "ERROR",
                "oldpeak_mV": np.nan,
            })
            print(f"[{idx}/{len(files)}] {base} FAIL: {e}")

    df = pd.DataFrame(rows)

    out_xlsx = proj_dir / "ecg_summary_results.xlsx"
    df.to_excel(out_xlsx, index=False)

    print(f"\n[DONE] Output Excel: {out_xlsx}")


if __name__ == "__main__":
    main()
