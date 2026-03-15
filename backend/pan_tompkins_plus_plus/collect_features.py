# -*- coding: utf-8 -*-
from pathlib import Path
from flask import Flask
import pandas as pd
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import database

# Base profile (later supplied by frontend)
DEFAULT_PATIENT_INFO = {
    "Age": 21,
    "Sex": "F",
    "ChestPainType": "NAP",
    "ExerciseAngina": "N",
    "RestingECG": False,
    "RestingBP": None,
    "Cholesterol": None,
    "FastingBS": None,
}
base_patient_info = DEFAULT_PATIENT_INFO.copy()

# Pick majority in ST_label and RestingECG column
# If tie, pick the one that appears last
def majority_vote(series):
    values = series.dropna()
    if values.empty:
        return None
    counts = values.value_counts()
    top = counts.max()
    candidates = counts[counts == top].index.tolist()
    if len(candidates) == 1:
        return candidates[0]
    last_idx = {val: values[values == val].index.max() for val in candidates}
    return max(last_idx, key=last_idx.get)

# Function that aggregates rest features
def collect_rest(df: pd.DataFrame) -> dict:
    return {
        "rest_max_hr": df["max_hr"].max(),
        "rest_mean_oldpeak": df["oldpeak"].mean(),
        "rest_resting_ecg_major": majority_vote(df["resting_ecg"]),
        "n_rest_windows": int(len(df)),
    }

# Function that aggregates exercise features
def collect_exercise(df: pd.DataFrame) -> dict:
    total = len(df)
    return {
        "ex_max_hr": df["max_hr"].max(),
        "ex_mean_oldpeak": df["oldpeak"].mean(),
        "ex_st_slope_major": majority_vote(df["st_label"]),
        "n_ex_windows": int(total),
    }

# TODO: check how to use window features and implement this.
# Also, I should process the rest/exercise issue.
def collect_features(df: pd.DataFrame, debug: bool = False, model_input_path: str = "../results_csv/model_input_features.csv", collectd_path: str = "../results_csv/collectd_features.csv") -> dict:
    global base_patient_info
    rest_feat = {}
    ex_feat = {}
    
    if not df.empty:
        df_rest = df[df["file"].astype(str).str.startswith("rest_")]
        df_ex   = df[df["file"].astype(str).str.startswith("exercise_")]

        if not df_rest.empty:
            rest_feat = collect_rest(df_rest)
        if not df_ex.empty:
            ex_feat   = collect_exercise(df_ex)
    # print("rest features:", rest_feat)
    # print("exercise features:", ex_feat)
    if rest_feat and ex_feat:
        # Delta oldpeak between exercise and rest
        delta_oldpeak = ex_feat["ex_mean_oldpeak"] - rest_feat["rest_mean_oldpeak"]
        # Infer ST_Slope from exercise ratios
        ex_st_slope = ex_feat["ex_st_slope_major"]
    else:
        delta_oldpeak = 0.0
        ex_st_slope = "Flat"

    # Write aggregated features
    collectd = {}
    for k, v in rest_feat.items():
        collectd[k] = v
    for k, v in ex_feat.items():
        collectd[k] = v
    collectd["delta_oldpeak"] = float(delta_oldpeak)
    collectd["ex_st_slope_major"] = ex_st_slope
    if debug:
        pd.DataFrame([collectd]).to_csv(collectd_path, index=False, encoding="utf-8-sig")

    # Export Final model input 
    model_input = base_patient_info.copy()
    model_input["MaxHR"] = float(ex_feat.get("ex_max_hr", rest_feat.get("rest_max_hr", 0)))
    model_input["ST_Slope"] = ex_st_slope
    model_input["Oldpeak"] = float(delta_oldpeak)
    model_input["RestingECG"] = "LVH" if base_patient_info["RestingECG"] else rest_feat.get("rest_resting_ecg_major", "Normal")

    if debug:
        print("[DONE] Aggregation finished")
        print(" collectd_features.csv:", collectd_path)
        print(" model_input_features.csv:", model_input_path)
        print(" n_rest_windows =", rest_feat.get("n_rest_windows", 0),
            "| n_ex_windows =", ex_feat["n_ex_windows"],
            "| delta_oldpeak =", float(delta_oldpeak),
            "| ST_Slope =", ex_st_slope,
            "| MaxHR =", model_input["MaxHR"])

    return model_input

def main():
    global base_patient_info
    base_dir = Path(__file__).resolve().parent
    out_dir = base_dir / "results_csv"
    out_dir.mkdir(parents=True, exist_ok=True)

    input_csv = out_dir / "window_features.csv"
    df = pd.read_csv(input_csv)
    
    model_input_path = out_dir / "model_input_features.csv"
    if not model_input_path.exists():
        raise FileNotFoundError(f"missing {model_input_path}")
    ipt = pd.read_csv(model_input_path)
    if ipt.empty:
        raise ValueError("model_input_features.csv is empty")
    base_patient_info["Age"] = int(ipt.iloc[0]["Age"])
    base_patient_info["Sex"] = str(ipt.iloc[0]["Sex"])
    base_patient_info["ChestPainType"] = str(ipt.iloc[0]["ChestPainType"])
    base_patient_info["ExerciseAngina"] = str(ipt.iloc[0]["ExerciseAngina"])

    collectd_path = out_dir / "collectd_features.csv"
    model_input = collect_features(df, True, model_input_path, collectd_path)
    pd.DataFrame([model_input]).to_csv(model_input_path, index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    main()
