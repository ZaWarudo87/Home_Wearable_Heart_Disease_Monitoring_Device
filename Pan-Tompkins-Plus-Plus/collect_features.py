# -*- coding: utf-8 -*-
from pathlib import Path
import pandas as pd

# Base profile (later supplied by frontend)
base_patient_info = {
    "Age": 21,
    "Sex": "F",
    "ChestPainType": "NAP",
    "ExerciseAngina": "N",
}

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

def main():
    base_dir = Path(__file__).resolve().parent
    
    # Load per-window features produced by address_features.py
    in_csv = base_dir / "results_csv" / "window_features.csv"
    if not in_csv.exists():
        raise FileNotFoundError(f"missing {in_csv}")

    df = pd.read_csv(in_csv)
    if df.empty:
        raise ValueError("window_features.csv is empty")

    # Split by filename prefix (This should be modified we should use a variable to classify rest/exercise)
    df_rest = df[df["file"].astype(str).str.startswith("rest_")]
    df_ex   = df[df["file"].astype(str).str.startswith("exercise_")]

    if df_rest.empty:
        raise ValueError("no rows starting with rest_")
    if df_ex.empty:
        raise ValueError("no rows starting with exercise_")

    rest_feat = collect_rest(df_rest)
    ex_feat   = collect_exercise(df_ex)

    # Delta oldpeak between exercise and rest
    delta_oldpeak = ex_feat["ex_mean_oldpeak"] - rest_feat["rest_mean_oldpeak"]

    # Infer ST_Slope from exercise ratios
    ex_st_slope = ex_feat["ex_st_slope_major"]

    # Write aggregated features
    collectd = {}
    for k, v in rest_feat.items():
        collectd[k] = v
    for k, v in ex_feat.items():
        collectd[k] = v
    collectd["delta_oldpeak"] = float(delta_oldpeak)
    collectd["ex_st_slope_major"] = ex_st_slope

    out_dir = base_dir / "results_csv"
    out_dir.mkdir(parents=True, exist_ok=True)

    collectd_path = out_dir / "collectd_features.csv"
    pd.DataFrame([collectd]).to_csv(collectd_path, index=False, encoding="utf-8-sig")

    # Export Final model input 
    model_input = base_patient_info.copy()
    model_input["MaxHR"] = float(ex_feat["ex_max_hr"])
    model_input["ST_Slope"] = ex_st_slope
    model_input["Oldpeak"] = float(delta_oldpeak)
    model_input["RestingECG"] = rest_feat["rest_resting_ecg_major"]

    model_input_path = out_dir / "model_input_features.csv"
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
