# -*- coding: utf-8 -*-
from pathlib import Path
import json
import pandas as pd
import joblib
import numpy as np

# ==========================================
# 1. 輔助函數：解包模型
# ==========================================
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

# ==========================================
# 2. 核心修正：手動特徵工程 (模擬 Training 的 drop_first=True)
# ==========================================
def manual_preprocess(raw_row: dict) -> pd.DataFrame:
    """
    手動建立特徵，確保與訓練時的 drop_first=True 邏輯一致。
    訓練時 Pandas get_dummies 預設會依字母排序類別，然後 drop 掉第一個。
    """
    row = {}

    # --- 數值欄位 (直接轉型) ---
    # 注意：因為沒有儲存 Scaler，這裡直接用原始數值
    # 對於樹模型 (RF, GBM, CatBoost) 這是可接受的
    row["Age"] = float(raw_row.get("Age", 0))
    row["MaxHR"] = float(raw_row.get("MaxHR", 0))
    row["Oldpeak"] = float(raw_row.get("Oldpeak", 0))

    # --- 類別欄位 (手動 One-Hot) ---
    
    # 1. Sex: [F, M] -> Drop F -> 保留 Sex_M
    sex = str(raw_row.get("Sex", "")).upper()
    row["Sex_M"] = 1.0 if sex == "M" else 0.0

    # 2. ExerciseAngina: [N, Y] -> Drop N -> 保留 ExerciseAngina_Y
    ea = str(raw_row.get("ExerciseAngina", "")).upper()
    row["ExerciseAngina_Y"] = 1.0 if ea == "Y" else 0.0

    # 3. ST_Slope: [Down, Flat, Up] -> Drop Down -> 保留 Flat, Up
    st = str(raw_row.get("ST_Slope", "")).capitalize()
    row["ST_Slope_Flat"] = 1.0 if st == "Flat" else 0.0
    row["ST_Slope_Up"]   = 1.0 if st == "Up" else 0.0
    # Down 隱含在全為 0 的情況中

    # 4. ChestPainType: [ASY, ATA, NAP, TA] -> Drop ASY -> 保留 ATA, NAP, TA
    cpt = str(raw_row.get("ChestPainType", "")).upper()
    row["ChestPainType_ATA"] = 1.0 if cpt == "ATA" else 0.0
    row["ChestPainType_NAP"] = 1.0 if cpt == "NAP" else 0.0
    row["ChestPainType_TA"]  = 1.0 if cpt == "TA" else 0.0
    # ASY 隱含在全為 0 的情況中

    return pd.DataFrame([row])

# ==========================================
# 3. 對齊特徵 (補 0 用的)
# ==========================================
def align_to_model_features(model, X_manual: pd.DataFrame) -> pd.DataFrame:
    """
    確保輸入模型的欄位順序與訓練時完全一致。
    如果有缺少的欄位 (例如訓練時有但手動建立漏了)，補 0。
    """
    if hasattr(model, "feature_names_in_"):
        # 這是最準確的方法，依照模型記憶的特徵名稱排序
        model_features = list(model.feature_names_in_)
        # reindex 會自動把缺少的欄位補 fill_value (0)
        X_aligned = X_manual.reindex(columns=model_features, fill_value=0.0)
        return X_aligned
    
    # 如果模型沒有紀錄特徵名稱 (較舊版本 sklearn)，直接回傳
    return X_manual

# ==========================================
# 4. 預測與工具函數
# ==========================================
def safe_predict(model, X: pd.DataFrame):
    try:
        pred = model.predict(X)
        pred_label = int(pred[0])  # 轉成 python int

        prob_pos = None
        if hasattr(model, "predict_proba"):
            try:
                proba = model.predict_proba(X)[0]
                prob_pos = float(proba[1]) if len(proba) >= 2 else float(proba[0])
            except:
                pass # 有些模型可能報錯
        return pred_label, prob_pos
    except Exception as e:
        raise RuntimeError(f"預測執行失敗: {str(e)}")

def to_py(obj):
    """將 numpy 數值轉為 python 原生型別以利 JSON 序列化"""
    if isinstance(obj, (np.int64, np.int32, int)):
        return int(obj)
    if isinstance(obj, (np.float64, np.float32, float)):
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
    
    # 請確保資料夾存在，這裡只載入樹模型 (因為只有它們能接受未 Scaled 的數據)
    model_paths = {
        "catboost": model_dir / "catboost_best.pkl",
        "gradient_boosting": model_dir / "gradient_boosting_best.pkl",
        "random_forest": model_dir / "random_forest_best.pkl",
    }

    out_dir = base_dir / "results_csv"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / "predictions_models.csv"
    out_json = out_dir / "prediction_ensemble.json"

    # --- 讀取輸入 ---
    if not input_csv.exists():
        print(f"[Error] 找不到 {input_csv}")
        return

    raw_df = pd.read_csv(input_csv)
    if raw_df.empty:
        print("[Error] 輸入 CSV 為空")
        return
    
    raw_row = raw_df.iloc[0].to_dict()
    print("\n[Input Data]:", raw_row)

    # --- 預處理 (關鍵修改點) ---
    # 使用手動建立的特徵，不依賴 get_dummies
    X_manual = manual_preprocess(raw_row)

    results = []
    probs = []

    for name, path in model_paths.items():
        try:
            if not path.exists():
                print(f"[Warn] 模型檔案不存在: {path}")
                continue
                
            loaded = joblib.load(path)
            model = unwrap_predictor(loaded)
            
            # 對齊特徵
            X_final = align_to_model_features(model, X_manual)
            
            # 取得特徵列表供紀錄
            features_used = X_final.columns.tolist()
            
            # 預測
            label, prob = safe_predict(model, X_final)
            
            results.append({
                "model": name,
                "pred_label": label,
                "prob_pos": prob,
                "n_features": len(features_used),
                "features_used": str(features_used) # 轉字串方便存 csv
            })
            
            if prob is not None:
                probs.append(prob)
                
            print(f"Model: {name} | Label: {label} | Prob: {prob:.4f}")

        except Exception as e:
            print(f"Model: {name} | Error: {e}")
            results.append({"model": name, "error": str(e)})

    # --- 彙整結果 ---
    if not results:
        print("沒有成功執行的模型預測。")
        return

    # 投票機制
    valid_labels = [r["pred_label"] for r in results if "pred_label" in r]
    if valid_labels:
        from collections import Counter
        final_label = Counter(valid_labels).most_common(1)[0][0]
        final_prob = sum(probs) / len(probs) if probs else 0.0
    else:
        final_label = None
        final_prob = None

    # --- 輸出 CSV ---
    df_out = pd.DataFrame(results)
    df_out.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # --- 輸出 JSON ---
    payload = {
        "input_raw": to_py(raw_row),
        "predictions": to_py(results),
        "ensemble": {
            "final_label": to_py(final_label),
            "final_prob": to_py(final_prob)
        }
    }

    if(final_label == 0):
        risk = '低風險'
    else:
        risk = '高風險'
    
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\n[Done] 最終預測結果: {risk} (平均機率: {final_prob:.2f})")
    print(f"結果已存至: {out_csv}")

if __name__ == "__main__":
    main()