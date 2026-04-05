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

EXPORTS_PATH = MODEL_DIR / "exported_models.json"


def load_model_bundles() -> dict[str, dict]:
    if not EXPORTS_PATH.exists():
        raise FileNotFoundError(f"missing metadata: {EXPORTS_PATH}")

    metadata = json.loads(EXPORTS_PATH.read_text(encoding="utf-8"))
    bundles = {}
    for export_entry in metadata["exports"]:
        model_path = MODEL_DIR / export_entry["model_path"]
        if not model_path.exists():
            raise FileNotFoundError(f"missing model: {model_path}")

        model = CatBoostClassifier()
        model.load_model(str(model_path))
        bundles[export_entry["model_name"]] = {
            "model": model,
            "config": export_entry,
        }
    return bundles


MODEL_BUNDLES = load_model_bundles()


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


def choose_model_name(raw_df: pd.DataFrame) -> str:
    if {"Cholesterol", "FastingBS"}.issubset(raw_df.columns):
        cholesterol = pd.to_numeric(raw_df["Cholesterol"], errors="coerce")
        fasting_bs = pd.to_numeric(raw_df["FastingBS"], errors="coerce")
        if cholesterol.notna().all() and fasting_bs.notna().all():
            return "catboost_10f"
    return "catboost_8f"


def preprocess_input(raw_df: pd.DataFrame, model_config: dict) -> pd.DataFrame:
    features = model_config["features"]
    prepared = pd.DataFrame(index=raw_df.index)

    for feature in features:
        if feature not in raw_df.columns:
            raise KeyError(f"missing feature: {feature}")
        prepared[feature] = raw_df[feature]

    for col, mapping in model_config["category_maps"].items():
        series = prepared[col].astype(str).fillna("Missing")
        unknown_values = sorted(set(series.unique()) - set(mapping.keys()))
        if unknown_values:
            raise ValueError(f"unknown category in {col}: {unknown_values}")
        prepared[col] = series.map(mapping).astype(int)

    for col, fill_value in model_config["numeric_imputer_stats"].items():
        prepared[col] = pd.to_numeric(prepared[col], errors="coerce").fillna(fill_value).astype(float)

    return prepared[features]


def risk_text_from_prob(prob: float, threshold: float) -> str:
    return "At Risk" if prob >= threshold else "No Risk"


def predict(raw_df: pd.DataFrame, debug: bool = False) -> dict:
    calc_start = time.time()
    model_name = choose_model_name(raw_df)
    bundle = MODEL_BUNDLES[model_name]
    model_config = bundle["config"]
    model = bundle["model"]
    X_ready = preprocess_input(raw_df.copy(), model_config)
    prob_pos = float(model.predict_proba(X_ready)[0][1])
    final_prob = round(prob_pos, 4)
    threshold = float(model_config["threshold"])

    feature_map = raw_df.iloc[0].to_dict()
    if debug:
        features_used_values = {feature: feature_map.get(feature) for feature in model_config["features"]}
    else:
        features_used_values = None

    out_dict = {
        "features_used_values": to_py(features_used_values),
        "ensemble": {
            "final_prob": to_py(final_prob),
            "risk_text": risk_text_from_prob(final_prob, threshold),
            "model_name": model_name,
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
