# -*- coding: utf-8 -*-
from pathlib import Path
import pandas as pd
from collections import Counter

# ===== 使用者基本資料（之後改成由前端傳入或讀檔）(KonoDiaDa 加油!!!!!!)=====
base_patient_info = {
    "Age": 21,
    "Sex": "F",
    "ChestPainType": "NAP",
    "ExerciseAngina": "N",
}

def majority_vote(series):
    cnt = Counter(series.dropna())
    return cnt.most_common(1)[0][0] if cnt else None

def collect_rest(df: pd.DataFrame) -> dict:
    return {
        "rest_mean_hr": df["max_hr"].mean(),
        "rest_mean_oldpeak": df["oldpeak"].mean(),
        "rest_min_oldpeak": df["oldpeak"].min(),
        "rest_st_label_major": majority_vote(df["st_label"]),
        "rest_resting_ecg_major": majority_vote(df["resting_ecg"]),
        "n_rest_windows": int(len(df)),
    }

def collect_exercise(df: pd.DataFrame) -> dict:
    total = len(df)
    label_cnt = Counter(df["st_label"])
    return {
        "ex_max_hr": df["max_hr"].max(),
        "ex_mean_hr": df["max_hr"].mean(),
        "ex_min_oldpeak": df["oldpeak"].min(),
        "ex_mean_oldpeak": df["oldpeak"].mean(),
        "ex_st_down_ratio": label_cnt.get("Down", 0) / total if total else 0.0,
        "ex_st_flat_ratio": label_cnt.get("Flat", 0) / total if total else 0.0,
        "ex_st_up_ratio": label_cnt.get("Up", 0) / total if total else 0.0,
        "n_ex_windows": int(total),
    }

def st_slope_from_ratios(ex_feat: dict) -> str:
    ratios = {
        "Down": ex_feat["ex_st_down_ratio"],
        "Flat": ex_feat["ex_st_flat_ratio"],
        "Up":   ex_feat["ex_st_up_ratio"],
    }
    return max(ratios, key=ratios.get)

def main():
    base_dir = Path(__file__).resolve().parent
    in_csv = base_dir / "results_csv" / "window_features.csv"
    if not in_csv.exists():
        raise FileNotFoundError(f"找不到 {in_csv}")
    
    out_dir = base_dir / "results_csv"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    model_input_path = out_dir / "model_input_features.csv"
    if not model_input_path.exists():
        raise FileNotFoundError(f"找不到 {model_input_path}")
    ipt = pd.read_csv(model_input_path)
    if ipt.empty:
        raise ValueError("model_input_features.csv 是空的")
    base_patient_info["Age"] = int(ipt.iloc[0]["Age"])
    base_patient_info["Sex"] = str(ipt.iloc[0]["Sex"])
    base_patient_info["ChestPainType"] = str(ipt.iloc[0]["ChestPainType"])
    base_patient_info["ExerciseAngina"] = str(ipt.iloc[0]["ExerciseAngina"])

    df = pd.read_csv(in_csv)
    if df.empty:
        raise ValueError("window_features.csv 是空的")

    df_rest = df[df["file"].astype(str).str.startswith("rest_")]
    df_ex   = df[df["file"].astype(str).str.startswith("exercise_")]

    if df_rest.empty:
        raise ValueError("找不到任何 rest_ 開頭的 rows")
    if df_ex.empty:
        raise ValueError("找不到任何 exercise_ 開頭的 rows")

    rest_feat = collect_rest(df_rest)
    ex_feat   = collect_exercise(df_ex)

    # delta oldpeak）
    delta_oldpeak = ex_feat["ex_mean_oldpeak"] - rest_feat["rest_mean_oldpeak"]

    # ST_Slope
    ex_st_slope = st_slope_from_ratios(ex_feat)

    # ===== 寫 collectd_features=====
    collectd = {}
    for k, v in rest_feat.items():
        collectd[k] = v
    for k, v in ex_feat.items():
        collectd[k] = v
    collectd["delta_oldpeak"] = float(delta_oldpeak)
    collectd["ex_st_slope_major"] = ex_st_slope

    collectd_path = out_dir / "collectd_features.csv"
    pd.DataFrame([collectd]).to_csv(collectd_path, index=False, encoding="utf-8-sig")

    # ===== 最終給 model 的 input=====
    model_input = base_patient_info.copy()
    model_input["MaxHR"] = float(ex_feat["ex_max_hr"])
    model_input["ST_Slope"] = ex_st_slope
    model_input["Oldpeak"] = float(delta_oldpeak)
    model_input["RestingECG"] = rest_feat["rest_resting_ecg_major"]

    pd.DataFrame([model_input]).to_csv(model_input_path, index=False, encoding="utf-8-sig")

    print("[DONE] Aggregation finished")
    print(" collectd_features.csv:", collectd_path)
    print(" model_input_features.csv:", model_input_path)
    print(" n_rest_windows =", rest_feat["n_rest_windows"],
          "| n_ex_windows =", ex_feat["n_ex_windows"],
          "| delta_oldpeak =", float(delta_oldpeak),
          "| ST_Slope =", ex_st_slope,
          "| MaxHR =", float(ex_feat["ex_max_hr"]))

if __name__ == "__main__":
    main()
