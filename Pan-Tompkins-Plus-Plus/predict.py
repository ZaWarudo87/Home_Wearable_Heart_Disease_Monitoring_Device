# -*- coding: utf-8 -*-
from pathlib import Path
import json
import pandas as pd
import joblib
import numpy as np


def unwrap_predictor(obj):
    if hasattr(obj, "predict"):
        return obj
    if isinstance(obj, dict):
        preferred_keys = ["model", "pipeline", "estimator", "clf", "classifier", "best_model"]
        for k in preferred_keys:
            if k in obj and hasattr(obj[k], "predict"):
                return obj[k]
        for _, v in obj.items():
            if hasattr(v, "predict"):
                return v
    raise TypeError(f"載入物件型別是 {type(obj)}，且找不到任何含 predict() 的模型。")


# ---------------------------------------------------------
# 1) 模型輸入：仍然產生 one-hot（模型要吃的）
# ---------------------------------------------------------
def manual_preprocess_onehot(raw_row: dict) -> pd.DataFrame:
    row = {}
    row["Age"] = float(raw_row.get("Age", 0))
    row["MaxHR"] = float(raw_row.get("MaxHR", 0))
    row["Oldpeak"] = float(raw_row.get("Oldpeak", 0))

    sex = str(raw_row.get("Sex", "")).strip().upper()
    row["Sex_M"] = 1.0 if sex == "M" else 0.0

    ea = str(raw_row.get("ExerciseAngina", "")).strip().upper()
    row["ExerciseAngina_Y"] = 1.0 if ea == "Y" else 0.0

    st = str(raw_row.get("ST_Slope", "")).strip().capitalize()
    row["ST_Slope_Flat"] = 1.0 if st == "Flat" else 0.0
    row["ST_Slope_Up"] = 1.0 if st == "Up" else 0.0

    cpt = str(raw_row.get("ChestPainType", "")).strip().upper()
    row["ChestPainType_ATA"] = 1.0 if cpt == "ATA" else 0.0
    row["ChestPainType_NAP"] = 1.0 if cpt == "NAP" else 0.0
    row["ChestPainType_TA"] = 1.0 if cpt == "TA" else 0.0

    return pd.DataFrame([row])


def align_to_model_features(model, X_manual: pd.DataFrame) -> pd.DataFrame:
    if hasattr(model, "feature_names_in_"):
        model_features = list(model.feature_names_in_)
        return X_manual.reindex(columns=model_features, fill_value=0.0)
    return X_manual


def safe_predict_proba_pos(model, X: pd.DataFrame):
    if not hasattr(model, "predict_proba"):
        return None
    proba = model.predict_proba(X)[0]
    return float(proba[1]) if len(proba) >= 2 else float(proba[0])


def to_py(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, dict):
        return {k: to_py(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_py(v) for v in obj]
    return obj


# ---------------------------------------------------------
# 2) 輸出：把 one-hot 還原成「分類型 key」
# ---------------------------------------------------------
def decode_onehot_to_categorical(x: dict) -> dict:
    """
    x 是模型對齊後的一列（dict，含 Age/MaxHR/Oldpeak + one-hot）
    回傳：人類可讀的分類型 features
    """
    out = {}
    out["Age"] = float(x.get("Age", 0.0))
    out["MaxHR"] = float(x.get("MaxHR", 0.0))
    out["Oldpeak"] = float(x.get("Oldpeak", 0.0))

    # Sex
    sex_m = float(x.get("Sex_M", 0.0))
    out["Sex"] = "M" if sex_m == 1.0 else "F"

    # ExerciseAngina
    ea_y = float(x.get("ExerciseAngina_Y", 0.0))
    out["ExerciseAngina"] = "Y" if ea_y == 1.0 else "N"

    # ST_Slope: Flat / Up / Down(baseline)
    st_flat = float(x.get("ST_Slope_Flat", 0.0))
    st_up = float(x.get("ST_Slope_Up", 0.0))
    if st_up == 1.0:
        out["ST_Slope"] = "Up"
    elif st_flat == 1.0:
        out["ST_Slope"] = "Flat"
    else:
        out["ST_Slope"] = "Down"

    # ChestPainType: ATA / NAP / TA / ASY(baseline)
    c_ata = float(x.get("ChestPainType_ATA", 0.0))
    c_nap = float(x.get("ChestPainType_NAP", 0.0))
    c_ta  = float(x.get("ChestPainType_TA", 0.0))
    if c_ata == 1.0:
        out["ChestPainType"] = "ATA"
    elif c_nap == 1.0:
        out["ChestPainType"] = "NAP"
    elif c_ta == 1.0:
        out["ChestPainType"] = "TA"
    else:
        out["ChestPainType"] = "ASY"

    return out


def main():
    base_dir = Path(__file__).resolve().parent
    input_csv = base_dir / "results_csv" / "model_input_features.csv"
    model_dir = base_dir / "model"

    model_paths = [
        model_dir / "catboost_best.pkl",
        model_dir / "gradient_boosting_best.pkl",
        model_dir / "random_forest_best.pkl",
    ]

    out_dir = base_dir / "results_csv"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "prediction_ensemble.json"

    if not input_csv.exists():
        print(f"[Error] 找不到 {input_csv}")
        return

    raw_df = pd.read_csv(input_csv)
    if raw_df.empty or len(raw_df) != 1:
        print("[Error] model_input_features.csv 必須且只能有 1 row")
        return

    raw_row = raw_df.iloc[0].to_dict()
    print("\n[Input Data]:", raw_row)

    # 模型輸入（one-hot）
    X_manual = manual_preprocess_onehot(raw_row)

    probs = []
    decoded_features = None  # 只需要一份，給前端看

    for mp in model_paths:
        if not mp.exists():
            continue

        loaded = joblib.load(mp)
        model = unwrap_predictor(loaded)

        X_final = align_to_model_features(model, X_manual)

        # 取第一個可用模型的對齊後輸入，轉成分類型輸出
        if decoded_features is None:
            x_dict = to_py(X_final.iloc[0].to_dict())
            decoded_features = decode_onehot_to_categorical(x_dict)

        p = safe_predict_proba_pos(model, X_final)
        if p is not None:
            probs.append(p)

    final_prob = (sum(probs) / len(probs)) if probs else None
    risk_text = None
    if final_prob is not None:
        risk_text = "高風險" if final_prob >= 0.5 else "低風險"

    output_dict = {
        "features_used_values": to_py(decoded_features),
        "ensemble": {
            "final_prob": to_py(final_prob),
            "risk_text": risk_text
        }
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(output_dict, f, ensure_ascii=False, indent=2)

    print("\n[Done] JSON saved:", out_json)
    print(json.dumps(output_dict, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
