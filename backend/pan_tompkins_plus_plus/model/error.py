# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import joblib

from pathlib import Path
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    mean_squared_error,
    precision_recall_fscore_support,
    roc_auc_score,
)
import matplotlib.pyplot as plt


base = Path(__file__).resolve().parent
train_path = base / "heart_train.csv"
thresholds = [0.4, 0.5]

df = pd.read_csv(train_path)
selected_features = [
    "Age",
    "Sex",
    "ChestPainType",
    "MaxHR",
    "ExerciseAngina",
    "Oldpeak",
    "ST_Slope",
    "RestingECG",
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
        for key in preferred_keys:
            if key in obj and hasattr(obj[key], "predict"):
                return obj[key]
        for _, value in obj.items():
            if hasattr(value, "predict"):
                return value
    raise TypeError(f"Cannot unwrap predictor from {type(obj)}")


def make_metric_row(threshold, split, pred_arr, prob_arr, y_true):
    cm = confusion_matrix(y_true, pred_arr, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    pr, rc, f1, _ = precision_recall_fscore_support(
        y_true, pred_arr, average="binary", zero_division=0
    )

    return {
        "model": "ensemble_mean_proba",
        "threshold": threshold,
        "split": split,
        "accuracy": accuracy_score(y_true, pred_arr),
        "precision": pr,
        "recall": rc,
        "f1": f1,
        "auc": roc_auc_score(y_true, prob_arr),
        "rmse": np.sqrt(mean_squared_error(y_true, prob_arr)),
        "errors": int((pred_arr != y_true).sum()),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }, cm


def save_confusion_matrix_png(cm, threshold, split):
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    im = ax.imshow(cm, cmap="Blues", interpolation="nearest")
    vmax = im.norm.vmax
    thresh = vmax * 0.6

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            color = "white" if cm[i, j] >= thresh else "black"
            ax.text(j, i, f"{cm[i, j]}", ha="center", va="center", color=color, fontsize=12)

    ax.set_xticks([0, 1], labels=["Pred 0", "Pred 1"])
    ax.set_yticks([0, 1], labels=["True 0", "True 1"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"Ensemble Mean Proba (thr={threshold}, {split})", pad=8)
    fig.tight_layout()
    out_path = base / f"ensemble_mean_proba_cm_thr_{threshold}_{split}.png"
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=369)

train_prob_list = []
oof_prob_list = []

for _, path in model_paths.items():
    model = unwrap_predictor(joblib.load(path))

    proba_train = model.predict_proba(X_raw)
    train_prob_list.append(proba_train[:, 1] if proba_train.shape[1] >= 2 else proba_train[:, 0])

    proba_oof = cross_val_predict(model, X_raw, y, cv=cv, method="predict_proba")
    oof_prob_list.append(proba_oof[:, 1] if proba_oof.shape[1] >= 2 else proba_oof[:, 0])

prob_mean_train = np.mean(train_prob_list, axis=0)
prob_mean_oof = np.mean(oof_prob_list, axis=0)

rows = []
for threshold in thresholds:
    pred_train = (prob_mean_train >= threshold).astype(int)
    row_train, cm_train = make_metric_row(threshold, "train", pred_train, prob_mean_train, y)
    rows.append(row_train)
    save_confusion_matrix_png(cm_train, threshold, "train")

    pred_test = (prob_mean_oof >= threshold).astype(int)
    row_test, cm_test = make_metric_row(threshold, "test_cv", pred_test, prob_mean_oof, y)
    rows.append(row_test)
    save_confusion_matrix_png(cm_test, threshold, "test_cv")

out_csv = base / "new_model_compare_train_test.csv"
pd.DataFrame(rows).to_csv(out_csv, index=False, encoding="utf-8-sig")
print(f"[OK] Wrote comparison CSV: {out_csv}")
