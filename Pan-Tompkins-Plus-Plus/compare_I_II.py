# -*- coding: utf-8 -*-
import os
from pathlib import Path
import glob
import numpy as np
import wfdb
import time
import matplotlib.pyplot as plt
import csv
from algos.pan_tompkins_plus_plus import Pan_Tompkins_Plus_Plus as RpeakDetection


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

        # 3) 輸出資料夾 + CSV
    out_dir = PROJ_DIR / "results_ptbxl"
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "lead_compare.csv"
    write_header = not csv_path.exists()
    csv_f = open(csv_path, "a", newline="", encoding="utf-8")
    csv_w = csv.writer(csv_f)
    if write_header:
        csv_w.writerow(["record", "fs", "lead", "peaks", "HR", "ST_Label", "Oldpeak", "OldpeakAbs", "ST_Slope"])

    t0 = time.time()
    for i, dat_path in enumerate(files, 1):
        base = Path(dat_path).with_suffix("")        # 去掉 .dat
        rec  = wfdb.rdrecord(str(base))              # 讀 .hea + .dat
        fs   = int(rec.fs)                           # records500 應為 500
        sig  = rec.p_signal                          # shape [N, 12]
        leads = rec.sig_name                         # 12 導程名稱

        # 4) 針對 Lead I 與 Lead II 都做一次（若存在）
        leads_to_check = []
        if "I" in leads:  leads_to_check.append("I")
        if "II" in leads: leads_to_check.append("II")
        if not leads_to_check:
            # 兩個都沒有時，fallback 到第 0 導程
            leads_to_check = [leads[LEAD_FALLBACK_IDX]]
            print(f"[{i}] 警告：{base.name} 無 Lead I/II，改用 {leads_to_check[0]}")

        results = []  # (lead_name, qrs_array, feats) for plotting & print

        for lead_name in leads_to_check:
            ch = leads.index(lead_name)
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

            # 6) 各導程存 peaks（檔名帶導程），並計算 features + 寫 CSV
            if SAVE_PEAKS:
                np.savetxt(out_dir / f"{base.name}_{lead_name}_rpeaks.txt", qrs, fmt="%d")

            feats = det.compute_ecg_features(ecg, fs)
            csv_w.writerow([
                base.name, fs, lead_name, int(qrs.size),
                feats["HR"], feats["ST_Label"], feats["Oldpeak"],
                feats["OldpeakAbs"], feats["ST_Slope"]
            ])

            # 把結果放到 results，用於終端列印 & 畫圖
            results.append((lead_name, qrs, feats))

        # 統一列印對照：I 與 II 的 peaks 與 features
        parts = [f"[{i}/{len(files)}] {base.name:>12s} | fs={fs}"]
        for ln, qrs_arr, ft in results:
            hr = (f"{ft['HR']:.1f}" if ft["HR"] == ft["HR"] else "NaN")  # NaN 安全印
            op = (f"{ft['Oldpeak']:.3f}" if ft["Oldpeak"] == ft["Oldpeak"] else "NaN")
            parts.append(f"{ln}:peaks={len(qrs_arr)} HR={hr} ST={ft['ST_Label']} Oldpeak={op}")
        print(" | ".join(parts))

        # 每 DRAW_EVERY 筆畫一次圖：同一張圖上把 I/II 疊在一起方便肉眼比對
        if DRAW_EVERY and (i % DRAW_EVERY == 1):
            plt.figure()
            for ln, qrs_arr, ft in results:
                ch = leads.index(ln)
                ecg = sig[:, ch]
                plt.plot(ecg, label=f"ECG {ln}")
                if qrs_arr.size:
                    plt.plot(qrs_arr, ecg[qrs_arr], 'o', label=f"R peaks {ln}")
            plt.title(f"{base.name} (fs={fs}) — Lead I vs II")
            plt.xlabel("Sample"); plt.ylabel("mV"); plt.legend()
            plt.show()

    csv_f.close()
    print(f"完成。總耗時 {time.time()-t0:.2f}s；R-peak 與 CSV 在 {out_dir}")
