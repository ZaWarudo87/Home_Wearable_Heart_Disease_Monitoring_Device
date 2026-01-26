# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.metrics import confusion_matrix, accuracy_score, precision_recall_fscore_support
import matplotlib.pyplot as plt

base = Path(__file__).resolve().parent
train_path = base / "heart_train.csv"

df = pd.read_csv(train_path)
selected_features = [
    "Age", "Sex", "ChestPainType", "MaxHR", "ExerciseAngina", "Oldpeak", "ST_Slope"
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

preds = {}
probs = {}

for name, path in model_paths.items():
    model = unwrap_predictor(joblib.load(path))
    if hasattr(model, "feature_names_in_"):
        X = X_raw.reindex(columns=list(model.feature_names_in_), fill_value=0.0)
    else:
        X = X_raw
    pred = model.predict(X).astype(int)
    preds[name] = pred
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)
        probs[name] = proba[:, 1] if proba.shape[1] >= 2 else proba[:, 0]

# Ensemble: mean probability
prob_mean = np.mean(list(probs.values()), axis=0)
preds["ensemble_mean_proba"] = (prob_mean >= 0.5).astype(int)

# Ensemble: mean probability without LogisticRegression
if "new_LogisticRegression" in probs:
    probs_wo_log = {k: v for k, v in probs.items() if k != "new_LogisticRegression"}
    if probs_wo_log:
        prob_mean_2 = np.mean(list(probs_wo_log.values()), axis=0)
        preds["ensemble_mean_proba_wo_log"] = (prob_mean_2 >= 0.5).astype(int)

def build_metrics(label, pred_arr):
    cm = confusion_matrix(y, pred_arr, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    acc = accuracy_score(y, pred_arr)
    pr, rc, f1, _ = precision_recall_fscore_support(
        y, pred_arr, average="binary", zero_division=0
    )
    return {
        "model": label,
        "accuracy": acc,
        "precision": pr,
        "recall": rc,
        "f1": f1,
        "errors": int((pred_arr != y).sum()),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }

print("== Error types (0->1 = FP, 1->0 = FN) on heart_train.csv ==")
rows = []
for name, pred in preds.items():
    cm = confusion_matrix(y, pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    print("{:<24s} FP(0->1)={} FN(1->0)={} | TN={} TP={}".format(
        name, fp, fn, tn, tp
    ))
    rows.append(build_metrics(name, pred))

names = list(preds.keys())
errors = {name: set(np.where(preds[name] != y)[0]) for name in names}

common_all = set.intersection(*errors.values())
print("\n== Error overlap across all models ==")
print("errors common to all:", len(common_all))

base_models = ["new_CatBoost", "new_LogisticRegression", "new_GradientBoosting"]
print("\n== Pairwise error overlap (3 base models) ==")
for i in range(len(base_models)):
    for j in range(i + 1, len(base_models)):
        a, b = base_models[i], base_models[j]
        inter = errors[a] & errors[b]
        print("{} & {}: {}".format(a, b, len(inter)))

print("\n== Error type overlap across 3 base models ==")
fp_sets = {}
fn_sets = {}
for name in base_models:
    pred = preds[name]
    fp_sets[name] = set(np.where((y == 0) & (pred == 1))[0])
    fn_sets[name] = set(np.where((y == 1) & (pred == 0))[0])

fp_common = set.intersection(*fp_sets.values())
fn_common = set.intersection(*fn_sets.values())
print("FP common to all 3:", len(fp_common))
print("FN common to all 3:", len(fn_common))

# Confusion matrix plot for ensemble_mean_proba
if "ensemble_mean_proba" in preds:
    cm = confusion_matrix(y, preds["ensemble_mean_proba"], labels=[0, 1])
    fig, ax = plt.subplots(figsize=(4, 4))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Pred 0", "Pred 1"])
    ax.set_yticklabels(["True 0", "True 1"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    out_png = base / "ensemble_mean_proba_confusion_matrix.png"
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    print(f"[OK] Wrote confusion matrix image: {out_png}")

out_csv = base / "model_compare.csv"
pd.DataFrame(rows).to_csv(out_csv, index=False, encoding="utf-8-sig")
print(f"\n[OK] Wrote comparison CSV: {out_csv}")
