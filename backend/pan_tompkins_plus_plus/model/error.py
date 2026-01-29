# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    precision_recall_fscore_support,
    roc_auc_score,
    mean_squared_error,
)

base = Path(__file__).resolve().parent
train_path = base / "heart_train.csv"

df = pd.read_csv(train_path)
selected_features = [
    "Age", "Sex", "ChestPainType", "MaxHR", "ExerciseAngina", "Oldpeak", "ST_Slope", "RestingECG"
]
X_raw = df[selected_features].copy()
y = df["HeartDisease"].astype(int).to_numpy()

model_paths = {
    "new_CatBoost": base / "new_CatBoost.pkl",
    "new_LogisticRegression": base / "new_LogisticRegression.pkl",
    "new_GradientBoosting": base / "new_GradientBoosting.pkl",
}

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
    raise TypeError("Cannot unwrap predictor from {}".format(type(obj)))

def build_metrics(label, pred_arr, y_true, prob_arr=None):
    cm = confusion_matrix(y_true, pred_arr, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    acc = accuracy_score(y_true, pred_arr)
    pr, rc, f1, _ = precision_recall_fscore_support(
        y_true, pred_arr, average="binary", zero_division=0
    )
    auc = roc_auc_score(y_true, prob_arr) if prob_arr is not None else np.nan
    rmse = np.sqrt(mean_squared_error(y_true, prob_arr)) if prob_arr is not None else np.nan
    return {
        "model": label,
        "accuracy": acc,
        "precision": pr,
        "recall": rc,
        "f1": f1,
        "auc": auc,
        "rmse": rmse,
        "errors": int((pred_arr != y_true).sum()),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }

cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=369)

train_preds = {}
train_probs = {}
oof_preds = {}
oof_probs = {}

for name, path in model_paths.items():
    model = unwrap_predictor(joblib.load(path))

    # Train metrics (fit already in pkl)
    pred_train = model.predict(X_raw).astype(int)
    train_preds[name] = pred_train
    if hasattr(model, "predict_proba"):
        proba_train = model.predict_proba(X_raw)
        train_probs[name] = proba_train[:, 1] if proba_train.shape[1] >= 2 else proba_train[:, 0]

    # CV OOF metrics
    pred_oof = cross_val_predict(model, X_raw, y, cv=cv, method="predict")
    oof_preds[name] = pred_oof.astype(int)
    if hasattr(model, "predict_proba"):
        proba_oof = cross_val_predict(model, X_raw, y, cv=cv, method="predict_proba")
        oof_probs[name] = proba_oof[:, 1] if proba_oof.shape[1] >= 2 else proba_oof[:, 0]

# Ensembles (train)
prob_mean_train = np.mean(list(train_probs.values()), axis=0)
train_preds["ensemble_mean_proba"] = (prob_mean_train >= 0.5).astype(int)

probs_wo_log_train = {k: v for k, v in train_probs.items() if k != "new_LogisticRegression"}
if probs_wo_log_train:
    prob_mean_wo = np.mean(list(probs_wo_log_train.values()), axis=0)
    train_preds["ensemble_mean_proba_wo_log"] = (prob_mean_wo >= 0.5).astype(int)

# Ensembles (OOF)
prob_mean_oof = np.mean(list(oof_probs.values()), axis=0)
oof_preds["ensemble_mean_proba"] = (prob_mean_oof >= 0.5).astype(int)

probs_wo_log_oof = {k: v for k, v in oof_probs.items() if k != "new_LogisticRegression"}
if probs_wo_log_oof:
    prob_mean_wo_oof = np.mean(list(probs_wo_log_oof.values()), axis=0)
    oof_preds["ensemble_mean_proba_wo_log"] = (prob_mean_wo_oof >= 0.5).astype(int)

rows = []
for name, pred in train_preds.items():
    row = build_metrics(name, pred, y, train_probs.get(name))
    row["split"] = "train"
    rows.append(row)

for name, pred in oof_preds.items():
    row = build_metrics(name, pred, y, oof_probs.get(name))
    row["split"] = "test_cv"
    rows.append(row)

out_csv = base / "new_model_compare_train_test.csv"
pd.DataFrame(rows).to_csv(out_csv, index=False, encoding="utf-8-sig")
print(f"[OK] Wrote comparison CSV: {out_csv}")
