# -*- coding: utf-8 -*-
from pathlib import Path
import json
import pandas as pd
import joblib


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
    raise TypeError(f"找不到含 predict() 的模型，載入物件型別={type(obj)}")


def build_onehot_row(raw: dict) -> dict:
    """
    將原始輸入（含字串類別）轉成 one-hot + 數值欄位的 row(dict)。
    這裡的 one-hot 欄位命名，依照你 error 顯示的格式：
      ChestPainType_XXX, ExerciseAngina_Y, ST_Slope_Up/Flat/Down, Sex_M
    """
    row = {}

    # numeric
    row["Age"] = float(raw["Age"])
    row["MaxHR"] = float(raw["MaxHR"])
    row["Oldpeak"] = float(raw["Oldpeak"])

    # Sex -> Sex_M (F 就是 0)
    sex = str(raw["Sex"]).strip().upper()
    row["Sex_M"] = 1.0 if sex == "M" else 0.0

    # ChestPainType -> one-hot
    cpt = str(raw["ChestPainType"]).strip().upper()
    for k in ["ATA", "NAP", "TA", "ASY"]:
        row[f"ChestPainType_{k}"] = 1.0 if cpt == k else 0.0

    # ExerciseAngina -> ExerciseAngina_Y
    ea = str(raw["ExerciseAngina"]).strip().upper()
    row["ExerciseAngina_Y"] = 1.0 if ea == "Y" else 0.0

    # ST_Slope -> one-hot
    st = str(raw["ST_Slope"]).strip().capitalize()  # Up/Flat/Down
    for k in ["Up", "Flat", "Down"]:
        row[f"ST_Slope_{k}"] = 1.0 if st == k else 0.0

    return row


def align_to_feature_names(onehot_row: dict, feature_names) -> pd.DataFrame:
    """
    對齊到模型訓練時的 feature_names：
      - 缺的補 0
      - 多的丟掉
      - 順序照 feature_names
    """
    data = {}
    for fn in feature_names:
        data[fn] = onehot_row.get(fn, 0.0)
    return pd.DataFrame([data], columns=list(feature_names))


def safe_predict(model, X: pd.DataFrame):
    pred = model.predict(X)
    pred_label = pred[0]

    prob_pos = None
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        prob_pos = float(proba[1]) if len(proba) >= 2 else float(proba[0])

    return pred_label, prob_pos


def majority_vote(labels):
    from collections import Counter
    cnt = Counter(labels)
    return cnt.most_common(1)[0][0] if labels else None


def main():
    base_dir = Path(__file__).resolve().parent
    input_csv = base_dir / "results_csv" / "model_input_features.csv"

    model_dir = base_dir / "model"
    model_paths = {
        "catboost_best": model_dir / "catboost_best.pkl",
        "gradient_boosting_best": model_dir / "gradient_boosting_best.pkl",
        "random_forest_best": model_dir / "random_forest_best.pkl",
    }

    out_dir = base_dir / "results_csv"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_csv = out_dir / "predictions_models.csv"
    out_json = out_dir / "prediction_ensemble.json"

    if not input_csv.exists():
        raise FileNotFoundError(f"找不到 model input：{input_csv}")

    raw_df = pd.read_csv(input_csv)
    if raw_df.empty or len(raw_df) != 1:
        raise ValueError("model_input_features.csv 必須且只能有 1 row")

    raw = raw_df.iloc[0].to_dict()

    # 先把 raw 轉成 one-hot row
    onehot_row = build_onehot_row(raw)

    rows = []
    labels = []
    probs = []

    for name, mp in model_paths.items():
        try:
            raw_obj = joblib.load(mp)
            model = unwrap_predictor(raw_obj)

            # 取得模型期待的欄位（sklearn 通常有 feature_names_in_）
            if hasattr(model, "feature_names_in_"):
                feature_names = model.feature_names_in_
                X = align_to_feature_names(onehot_row, feature_names)
            else:
                # 若模型沒有提供 feature_names_in_，就先用 onehot 直接丟（可能仍會失敗）
                X = pd.DataFrame([onehot_row])

            pred_label, prob_pos = safe_predict(model, X)

            rows.append({"model": name, "pred_label": pred_label, "prob_pos": prob_pos})
            labels.append(pred_label)
            if prob_pos is not None:
                probs.append(prob_pos)

        except Exception as e:
            rows.append({"model": name, "pred_label": None, "prob_pos": None, "error": str(e)})

    df_out = pd.DataFrame(rows)
    df_out.to_csv(out_csv, index=False, encoding="utf-8-sig")

    final_label = majority_vote([r["pred_label"] for r in rows if r.get("pred_label") is not None])
    final_prob = float(sum(probs) / len(probs)) if probs else None

    payload = {
        "input_raw": raw,
        "input_onehot": onehot_row,
        "per_model": rows,
        "ensemble": {"final_label_majority": final_label, "final_prob_mean": final_prob}
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("[DONE] Predictions finished")
    print(" predictions_models.csv:", out_csv)
    print(" prediction_ensemble.json:", out_json)
    print(" ensemble final_label =", final_label, "| final_prob =", final_prob)
    print(df_out.to_string(index=False))


if __name__ == "__main__":
    main()
