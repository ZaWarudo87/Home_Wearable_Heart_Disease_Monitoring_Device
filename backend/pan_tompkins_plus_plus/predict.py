# -*- coding: utf-8 -*-
from pathlib import Path
import cpuinfo
import json
import pandas as pd
import numpy as np
import time

from catboost import CatBoostClassifier


BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "model"
OUT_DIR = BASE_DIR / "results_csv"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "catboost_8f"
EXPORTS_PATH = MODEL_DIR / "exported_models.json"


def load_model_bundle() -> tuple[CatBoostClassifier, dict]:
    if not EXPORTS_PATH.exists():
        raise FileNotFoundError(f"missing metadata: {EXPORTS_PATH}")

    metadata = json.loads(EXPORTS_PATH.read_text(encoding="utf-8"))
    export_entry = next((item for item in metadata["exports"] if item["model_name"] == MODEL_NAME), None)
    if export_entry is None:
        raise KeyError(f"missing export config for {MODEL_NAME}")

    model_path = MODEL_DIR / export_entry["model_path"]
    if not model_path.exists():
        raise FileNotFoundError(f"missing model: {model_path}")

    model = CatBoostClassifier()
    model.load_model(str(model_path))
    return model, export_entry


MODEL, MODEL_CONFIG = load_model_bundle()


def to_py(obj):
    if obj is None:
        return obj
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, dict):
        return {k: to_py(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_py(v) for v in obj]
    return obj


def preprocess_input(raw_df: pd.DataFrame) -> pd.DataFrame:
    features = MODEL_CONFIG["features"]
    prepared = pd.DataFrame(index=raw_df.index)

    for feature in features:
        if feature not in raw_df.columns:
            raise KeyError(f"missing feature: {feature}")
        prepared[feature] = raw_df[feature]

    for col, mapping in MODEL_CONFIG["category_maps"].items():
        series = prepared[col].astype(str).fillna("Missing")
        unknown_values = sorted(set(series.unique()) - set(mapping.keys()))
        if unknown_values:
            raise ValueError(f"unknown category in {col}: {unknown_values}")
        prepared[col] = series.map(mapping).astype(int)

    for col, fill_value in MODEL_CONFIG["numeric_imputer_stats"].items():
        prepared[col] = pd.to_numeric(prepared[col], errors="coerce").fillna(fill_value).astype(float)

    return prepared[features]


def risk_text_from_prob(prob: float, threshold: float) -> str:
    return "有風險" if prob >= threshold else "無風險"


def predict(raw_df: pd.DataFrame, debug: bool = False) -> dict:
    calc_start = time.time()
    X_ready = preprocess_input(raw_df.copy())
    prob_pos = float(MODEL.predict_proba(X_ready)[0][1])
    final_prob = round(prob_pos, 4)
    threshold = float(MODEL_CONFIG["threshold"])

    feature_map = raw_df.iloc[0].to_dict()
    if debug:
        features_used_values = {feature: feature_map.get(feature) for feature in MODEL_CONFIG["features"]}
    else:
        features_used_values = None

    out_dict = {
        "features_used_values": to_py(features_used_values),
        "ensemble": {
            "final_prob": to_py(final_prob),
            "risk_text": risk_text_from_prob(final_prob, threshold),
            "model_name": MODEL_NAME,
            "threshold": threshold,
        },
    }

    calc_time = time.time() - calc_start
    calc_time_csv = OUT_DIR / "prediction_time.csv"
    info = cpuinfo.get_cpu_info()
    if not calc_time_csv.exists():
        with open(calc_time_csv, "w", encoding="utf-8") as f:
            f.write("cpu,calc_time_seconds,date\n")
    with open(calc_time_csv, "a", encoding="utf-8") as f:
        f.write(
            f"{info['brand_raw']} {info['arch']} {info['hz_advertised_friendly']},"
            f"{calc_time},{time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

    return out_dict


def main():
    input_csv = OUT_DIR / "model_input_features.csv"
    out_json = OUT_DIR / "prediction_ensemble.json"

    if not input_csv.exists():
        print(f"[Error] missing input: {input_csv}")
        return

    raw_df = pd.read_csv(input_csv)
    if raw_df.empty:
        print("[Error] model_input_features.csv is empty")
        return

    out_dict = predict(raw_df, True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(out_dict, f, ensure_ascii=False, indent=2)
    print("\n[Done] predictions saved:")
    print(f"  {out_json}")


if __name__ == "__main__":
    main()
