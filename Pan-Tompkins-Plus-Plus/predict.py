# -*- coding: utf-8 -*-
from pathlib import Path
import sys
import json
import pandas as pd
import joblib
import numpy as np

# Compatibility: models saved when fix_suspicious_numeric lived in __main__
def _ensure_feature_utils(model_dir: Path):
    if str(model_dir) not in sys.path:
        sys.path.insert(0, str(model_dir))
    try:
        __import__("feature_utils")
    except Exception:
        return


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


def main():
    base_dir = Path(__file__).resolve().parent
    input_csv = base_dir / "results_csv" / "model_input_features.csv"
    model_dir = base_dir / "model"
    _ensure_feature_utils(model_dir)

    model_paths = [
        model_dir / "new_CatBoost.pkl",
        model_dir / "new_LogisticRegression.pkl",
        model_dir / "new_GradientBoosting.pkl",
    ]

    out_dir = base_dir / "results_csv"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / "predictions_models.csv"
    out_json = out_dir / "prediction_ensemble.json"

    if not input_csv.exists():
        print(f"[Error] missing input: {input_csv}")
        return

    raw_df = pd.read_csv(input_csv)
    if raw_df.empty:
        print("[Error] model_input_features.csv is empty")
        return

    X_raw = raw_df.copy()
    results = []
    probs = []

    for mp in model_paths:
        if not mp.exists():
            print(f"[Warn] missing model: {mp}")
            continue

        model = joblib.load(mp)
        pred = model.predict(X_raw)
        pred_label = int(pred[0])

        prob_pos = None
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X_raw)[0]
            prob_pos = float(proba[1]) if len(proba) >= 2 else float(proba[0])
            probs.append(prob_pos)

        results.append({
            "model": mp.name,
            "pred_label": pred_label,
            "prob_pos": prob_pos,
        })

    if not results:
        print("[Error] no models loaded")
        return

    final_prob = float(sum(probs) / len(probs)) if probs else None
    if final_prob is not None:
        final_prob = round(final_prob, 2)
    risk_text = None
    if final_prob is not None:
        risk_text = "高風險" if final_prob >= 0.5 else "低風險"

    feature_map = raw_df.iloc[0].to_dict()
    features_used_values = {
        "Age": float(feature_map.get("Age", 0)),
        "MaxHR": float(feature_map.get("MaxHR", 0)),
        "Oldpeak": float(feature_map.get("Oldpeak", 0)),
        "Sex": str(feature_map.get("Sex", "")),
        "ExerciseAngina": str(feature_map.get("ExerciseAngina", "")),
        "ST slope": str(feature_map.get("ST_Slope", "")),
        "ChestPainType": str(feature_map.get("ChestPainType", "")),
    }

    payload = {
        "features_used_values": to_py(features_used_values),
        "ensemble": {
            "final_prob": to_py(final_prob),
            "risk_text": risk_text,
        }
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("\n[Done] predictions saved:")
    print(f"  {out_json}")


if __name__ == "__main__":
    main()
