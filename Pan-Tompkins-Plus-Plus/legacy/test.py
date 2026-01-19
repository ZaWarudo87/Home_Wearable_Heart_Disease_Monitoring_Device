# -*- coding: utf-8 -*-
import os
from pathlib import Path
import glob
import numpy as np
import time
import matplotlib.pyplot as plt
import csv
from scipy import signal

from algos.pan_tompkins_plus_plus import Pan_Tompkins_Plus_Plus as RpeakDetection

def filter_for_st(sig, fs): #for st slope hp 0.5HZ lp 35Hz

    sig = np.asarray(sig, dtype=float)

    # 1) High-pass 0.5 Hz
    hp_cut = 0.5          # Hz
    hp_N   = 3            # 3rd-order
    Wn_hp  = hp_cut * 2.0 / fs
    bhp, ahp = signal.butter(hp_N, Wn_hp, btype='highpass')
    sig_hp = signal.filtfilt(bhp, ahp, sig)

    # 2) Low-pass 35 Hz
    lp_cut = 35.0         # or try 40 Hz 
    lp_N   = 3
    Wn_lp  = lp_cut * 2.0 / fs
    blp, alp = signal.butter(lp_N, Wn_lp, btype='lowpass')
    sig_bp = signal.filtfilt(blp, alp, sig_hp)

    return sig_bp


# ===== 可調參數 =====
DRAW_EVERY   = 1            # 每隔幾筆畫一次圖（避免一堆視窗）
SAVE_PEAKS   = True         # 是否把偵測到的 R-peak 存檔
MAX_FILES    = None         # 先跑前 N 筆；全跑設 None
RESAMPLE_TO  = None         # 例如 250 代表重採樣到 250 Hz；None 代表不重採樣
TIMESTAMP_COL = "timestamp" # CSV 欄名（秒）
VALUE_COL     = "ecg_value" # CSV 欄名（ADC counts 或 mV）

# 讀CSV
def read_csv_one(path):

    ts, val = [], [] #ts 放時間 val 放ECG value
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = [h.strip() for h in reader.fieldnames] if reader.fieldnames else [] # 移除欄名前後空白
        name_map = {h.strip(): h for h in reader.fieldnames} if reader.fieldnames else {}
        #檢查必要欄位
        if TIMESTAMP_COL not in fields or VALUE_COL not in fields:
            raise ValueError(f"{path} 缺少必要欄位 {TIMESTAMP_COL},{VALUE_COL} (header={reader.fieldnames})")
        for row in reader:
            try:
                ts.append(float(row[name_map[TIMESTAMP_COL]].strip()))
                val.append(float(row[name_map[VALUE_COL]].strip()))
            except Exception:
                # 跳過壞行
                continue
    ts = np.asarray(ts, dtype=float)
    val = np.asarray(val, dtype=float)
    if ts.size < 3:
        raise ValueError(f"{path} 太短，無法估計取樣率")
    return ts, val

def estimate_fs(timestamps):
    """
    以 median Δt 估計取樣率，返回 (fs_float, dt_stats)
    """
    dt = np.diff(timestamps)
    dt = dt[(dt > 0) & np.isfinite(dt)] #保留正數且有限的時間差
    if dt.size == 0:
        raise ValueError("timestamp 無法估計 dt")
    fs = 1.0 / np.median(dt)
    stats = dict(dt_ms_mean=np.mean(dt)*1000.0,
                 dt_ms_std=np.std(dt)*1000.0,
                 dt_ms_min=np.min(dt)*1000.0,
                 dt_ms_max=np.max(dt)*1000.0)
    return float(fs), stats

def linear_resample(ts, x, fs_target):

    t0, t1 = ts[0], ts[-1]
    n = int(np.floor((t1 - t0) * fs_target)) + 1
    if n <= 1:
        # 太短則不重採樣
        return x.copy(), fs_target, ts.copy()
    t_new = t0 + np.arange(n) / fs_target
    x_new = np.interp(t_new, ts, x)
    return x_new, fs_target, t_new

if __name__ == "__main__":
    det = RpeakDetection()

    # ---- CSV 目錄（固定）----
    PROJ_DIR = Path(__file__).resolve().parent     # 主程式所在資料夾
    CSV_DIR = PROJ_DIR / "ECG_DATA"                # 只看這個資料夾

    if not CSV_DIR.exists():
        raise FileNotFoundError(f"找不到 ECG_DATA 資料夾：{CSV_DIR}")

    files = sorted(glob.glob(str(CSV_DIR / "*.csv")))  # 只讀 ECG_DATA/*.csv
    if not files:
        raise FileNotFoundError(f"ECG_DATA 資料夾裡找不到任何 CSV 檔案：{CSV_DIR}/*.csv")

    if MAX_FILES:
        files = files[:MAX_FILES]

    print(f"[INFO] 使用的 CSV 目錄：{CSV_DIR}")
    print(f"[INFO] 找到 {len(files)} 個 CSV：", [Path(f).name for f in files][:5], "..." if len(files) > 5 else "")
    # ---- end locator ----

    # 2) 輸出資料夾
    out_dir = PROJ_DIR / "results_csv"
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    for i, csv_path in enumerate(files, 1):
        base = Path(csv_path).stem

        # 3) 讀 CSV + 估 fs
        ts, ecg = read_csv_one(csv_path)
        fs_est, dt_stats = estimate_fs(ts)

        # 4) 是否重採樣
        if RESAMPLE_TO is not None and RESAMPLE_TO > 0:
            ecg_use, fs_float, ts_rs = linear_resample(ts, ecg, float(RESAMPLE_TO))
            t_axis = np.arange(ecg_use.size)  # sample index
        else:
            ecg_use, fs_float, ts_rs = ecg, fs_est, ts
            t_axis = np.arange(ecg_use.size)

        # 後面 R-peak、feature、畫圖的部份全部維持原本那樣 ...


        # 5) R-peak 偵測 + 不應期去重（200 ms）
        fs_i = int(round(fs_float))  # 轉整數，避免報錯
        qrs = np.asarray(det.rpeak_detection(ecg_use, fs_i), dtype=int)

        #過濾假的 R-peak (200ms內不應有另一個peak)
        if qrs.size:
            refractory = int(round(0.200 * fs_i)) #應有幾個樣本
            keep = [qrs[0]]
            for k in range(1, len(qrs)):
                if qrs[k] - keep[-1] >= refractory:
                    keep.append(qrs[k])
            qrs = np.asarray(keep, dtype=int)

        # 6) 顯示/輸出
        print(f"[{i}/{len(files)}] {base:>20s} | fs≈{fs_est:.2f} Hz"
              f" (dt_mean={dt_stats['dt_ms_mean']:.3f} ms, std={dt_stats['dt_ms_std']:.3f} ms)"
              f" | peaks={len(qrs)} ")

        if SAVE_PEAKS:
            if qrs.size:
                peak_ts = ts_rs[qrs]   # 與 sample index 對齊的 timestamp
                out_np = np.column_stack([qrs, peak_ts])
            else:
                out_np = np.empty((0, 2), dtype=float)
            np.savetxt(out_dir / f"{base}_rpeaks.csv",
                       out_np,
                       fmt=["%d", "%.9f"],
                       delimiter=",",
                       header="sample_index,timestamp_s",
                       comments="")
            
            # === (A) 計算兩種版本的 feature ===
            # 建議都用 ecg_use（跟 R-peak 偵測同一個訊號 & fs）
            features = det.compute_ecg_features(ecg_use, fs_i)
            features_stfilt = det.compute_ecg_features_stfilt(ecg_use, fs_i)   # ST 濾波版本


            print("result :")
            print(f"  MAX HR={features['HR']:.1f} bpm, "
                  f"ST_label={features_stfilt['ST_Label']}, "
                  f"Oldpeak={features_stfilt['Oldpeak']:.3f} mV")

            # === (B) 專門給 ST 用的濾波波形（用來畫圖比較） ===
            ecg_stfilt_full = filter_for_st(ecg_use, fs_i)   # 跟 ecg_use 對齊
           
            # === 只取前 N 秒，看得比較清楚 ===
            max_t =30  # 秒
            time_axis_sec = (ts_rs - ts_rs[0])
            mask = time_axis_sec <= max_t

            ecg_show_raw    = ecg_use[mask]
            ecg_show_stfilt = ecg_stfilt_full[mask]
            t_show          = time_axis_sec[mask]

            plt.figure()
            # 原始波形
            plt.plot(t_show, ecg_show_raw, label="ECG raw")
            # ST 濾波後波形（0.5–35 Hz）
            plt.plot(t_show, ecg_show_stfilt, label="ECG ST-filtered (0.5–35 Hz)", linewidth=2)

            # 如果 R-peak 在這段範圍內，就畫出來（還是用原始 ecg_use 的 peak）
            if qrs.size:
                qrs_mask = qrs[(qrs >= 0) & (qrs < len(ecg_use))]
                peak_times  = time_axis_sec[qrs_mask]
                peak_values = ecg_use[qrs_mask]
                valid = (peak_times >= 0.0) & (peak_times <= max_t)
                plt.plot(peak_times[valid], peak_values[valid], 'o', label="R peaks (raw)")

                # === 標示每拍的 ST 段（R+60ms ~ R+80ms），兩條波形都看得到 ===
                st_s = int(round(0.06 * fs_i))  # 60 ms
                st_e = int(round(0.08 * fs_i))  # 80 ms

                first_span = True
                for r in qrs_mask:
                    s_idx = r + st_s
                    e_idx = r + st_e
                    if s_idx < 0 or e_idx >= len(ecg_use):
                        continue

                    t_s = time_axis_sec[s_idx]
                    t_e = time_axis_sec[e_idx]

                    if t_e < 0.0 or t_s > max_t:
                        continue

                    # 半透明色塊：ST 量測窗
                    plt.axvspan(max(t_s, 0.0), min(t_e, max_t),
                                alpha=0.2,
                                label="ST 60–80 ms window" if first_span else None)

                    # 在 ST 段畫水平線：可以選擇畫 raw 或 ST-filtered 的平均
                    y_mean_raw    = float(np.mean(ecg_use[s_idx:e_idx]))
                    y_mean_stfilt = float(np.mean(ecg_stfilt_full[s_idx:e_idx]))

                    plt.plot([t_s, t_e], [y_mean_raw,    y_mean_raw],    linewidth=1, linestyle="--")
                    plt.plot([t_s, t_e], [y_mean_stfilt, y_mean_stfilt], linewidth=2)

                    first_span = False

            title_suffix = f" (fs≈{fs_est:.2f} Hz" + ("" if not RESAMPLE_TO else f" -> {fs_i} Hz") + ")"
            plt.title(f"{base} first {max_t:.0f} sec ECG{title_suffix}")
            plt.xlabel("Time (s)")
            plt.ylabel("ECG units")
            plt.legend()
            plt.tight_layout()
            plt.show()






