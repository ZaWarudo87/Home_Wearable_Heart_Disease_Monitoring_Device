# -*- coding: utf-8 -*-
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import wfdb

from algos.pan_tompkins_plus_plus import Pan_Tompkins_Plus_Plus as RpeakDetection
MAX_T_SEC = 10.0

def filter_for_rpeak(sig, fs):
    sig = np.asarray(sig, dtype=float)
    fs_i = int(round(fs))

    if fs_i == 200:
        sig = sig - np.mean(sig)

        # lowpass 12 Hz
        Wn = 12.0 * 2.0 / fs_i
        N = 3
        b_lp, a_lp = signal.butter(N, Wn, btype="lowpass")
        ecg_l = signal.filtfilt(b_lp, a_lp, sig)
        m = np.max(np.abs(ecg_l))
        if m > 0:
            ecg_l = ecg_l / m

        # highpass 5 Hz
        Wn = 5.0 * 2.0 / fs_i
        N = 3
        b_hp, a_hp = signal.butter(N, Wn, btype="highpass")
        ecg_h = signal.filtfilt(b_hp, a_hp, ecg_l, padlen=3*(max(len(a_hp), len(b_hp))-1))
        m = np.max(np.abs(ecg_h))
        if m > 0:
            ecg_h = ecg_h / m
    else:
        f1, f2 = 5.0, 18.0
        Wn = [f1 * 2.0 / fs, f2 * 2.0 / fs]
        N = 3
        b_bp, a_bp = signal.butter(N=N, Wn=Wn, btype="bandpass")
        ecg_h = signal.filtfilt(b_bp, a_bp, sig, padlen=3*(max(len(a_bp), len(b_bp)) - 1))
        m = np.max(np.abs(ecg_h))
        if m > 0:
            ecg_h = ecg_h / m

    return ecg_h

if __name__ == "__main__":
    PROJ_DIR = Path(__file__).resolve().parent
    DATA_DIR = PROJ_DIR / "ECG_DATA"

    record_name = "00002_hr"  
    record_path = str(DATA_DIR / record_name)

    # 讀 WFDB record（.hea + .dat）
    rec = wfdb.rdrecord(record_path)
    fs = float(rec.fs)
    fs_i = int(round(fs))

    # 取第一個通道
    x_full = rec.p_signal[:, 0] if rec.p_signal is not None else rec.d_signal[:, 0].astype(float)

    # 只取前 10 秒
    n = int(min(len(x_full), round(MAX_T_SEC * fs)))
    x = x_full[:n]
    t = np.arange(n) / fs

  
    det = RpeakDetection()
    qrs = np.asarray(det.rpeak_detection(x, fs_i), dtype=int)

    #  濾波後波形
    y = filter_for_rpeak(x, fs)

    # 畫圖 + 標 R peaks（
    plt.figure()
    plt.plot(t, y, label="ECG Rpeak-filtered")

    if qrs.size:
        qrs = qrs[(qrs >= 0) & (qrs < n)]
        plt.plot(t[qrs], y[qrs], 'o', label=f"R peaks (n={len(qrs)})")

    plt.title(f"{record_name} | first {MAX_T_SEC:.1f} sec | fs={fs:.2f} Hz")
    plt.xlabel("Time (s)")
    plt.ylabel("Normalized amplitude")
    plt.legend()
    plt.tight_layout()
    plt.show()
