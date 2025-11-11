# -*- coding: utf-8 -*-
import os
from pathlib import Path
import glob
import numpy as np
import wfdb
import time
import matplotlib.pyplot as plt

from algos.pan_tompkins_plus_plus import Pan_Tompkins_Plus_Plus as RpeakDetection

import csv



# ===== 可調參數 =====
DRAW_EVERY = 1       # 每隔幾筆畫一次圖（避免 1000 張視窗）
SAVE_PEAKS = True     # 是否把偵測到的 R-peak 索引存成 .txt
LEAD_FALLBACK_IDX = 0 # 找不到 lead II 時用哪個導程
MAX_FILES = None      # 想先測 50 筆就設 50；要全跑就設 None

if __name__ == "__main__":
    det = RpeakDetection()

    # 1) 路徑：main 在 Pan-Tompkins-Plus-Plus，資料在兄弟資料夾 ECG-Live-Filter
    PROJ_DIR = Path(__file__).resolve().parent
    DATA_ROOT = PROJ_DIR.parent / "ECG-Live-Filter" / "physionet.org" / "files" / "ptb-xl" / "1.0.3"
    # 這批是 500 Hz 的 high-resolution 記錄
    REC_DIR = DATA_ROOT / "records500"

    # 2) 抓所有 *_hr.dat（會掃到 00000, 00001, ... 子資料夾）
    files = sorted(glob.glob(str(REC_DIR / "*" / "*_hr.dat")))
    if MAX_FILES:
        files = files[:MAX_FILES]

    if not files:
        raise FileNotFoundError(f"找不到任何檔案：{REC_DIR}/*/*_hr.dat")

    print(f"找到 {len(files)} 筆 PTB-XL 記錄（預期 1000 筆）")

    # 3) 輸出資料夾
    out_dir = PROJ_DIR / "results_ptbxl"
    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    for i, dat_path in enumerate(files, 1):
        base = Path(dat_path).with_suffix("")        # 去掉 .dat
        rec  = wfdb.rdrecord(str(base))              # 讀 .hea + .dat
        fs   = int(rec.fs)                           # records500 應為 500
        sig  = rec.p_signal                          # shape [N, 12]
        leads = rec.sig_name                         # 12 導程名稱

        # 4) 選擇 lead II（沒 II 就 fallback）
        if "I" in leads:
            ch = leads.index("I")
        else:
            ch = LEAD_FALLBACK_IDX
            print(f"[{i}] 警告：{base.name} 無 lead II，改用 {leads[ch]}")
        ecg = sig[:, ch]

        # 5) R-peak 偵測 + 200 ms 不應期去重
        qrs = det.rpeak_detection(ecg, fs)
        qrs = np.asarray(qrs, dtype=int)
        if qrs.size:
            refractory = int(0.200 * fs)
            keep = [qrs[0]]
            for k in range(1, len(qrs)):
                if qrs[k] - keep[-1] >= refractory:
                    keep.append(qrs[k])
            qrs = np.asarray(keep, dtype=int)

        # 6) 輸出
        print(f"[{i}/{len(files)}] {base.name:>12s} | fs={fs} | peaks={len(qrs)}")

        if SAVE_PEAKS:
            np.savetxt(out_dir / f"{base.name}_rpeaks.txt", qrs, fmt="%d")

        # 每 DRAW_EVERY 筆畫一次圖，避免開太多視窗
            
            features = det.compute_ecg_features(ecg, fs)
            print(f"Record {base.name}: HR={features['HR']:.1f} bpm, "
            f"ST_label={features['ST_Label']}, Oldpeak={features['Oldpeak']:.3f} mV")
            if i % DRAW_EVERY == 1:
                plt.figure()
                plt.plot(ecg, label=f"ECG lead {leads[ch]}")
                if qrs.size:
                    plt.plot(qrs, ecg[qrs], 'o', label="R peaks")
                plt.title(f"{base.name} (fs={fs})")
                plt.xlabel("Sample")
                plt.ylabel("mV")
                plt.legend()
                plt.show()

    print(f"完成。總耗時 {time.time()-t0:.2f}s；R-peak 檔案輸出在 {out_dir}")
