# ==================== Libraries ====================
import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.impute import SimpleImputer, KNNImputer

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier

from catboost import CatBoostClassifier


# ==================== Config ====================
RANDOM_STATE = 369
TOP_K = 3

# Keep only the features you said you need
FEATURES = ['Age', 'Sex', 'ChestPainType', 'MaxHR', 'ExerciseAngina', 'Oldpeak', 'ST_Slope', 'RestingECG']
TARGET = 'HeartDisease'

CAT_COL = ['Sex', 'ChestPainType', 'ExerciseAngina', 'ST_Slope', 'RestingECG']
NUM_COL = ['Age', 'MaxHR', 'Oldpeak']

# ==================== Load Data ====================
df_train = pd.read_csv("heart_train.csv")
df_test  = pd.read_csv("heart_test.csv")

X_train_raw = df_train[FEATURES].copy()
y_train = df_train[TARGET].copy()
X_test_raw  = df_test[FEATURES].copy()

# ==================== Custom Cleaning (within Pipeline) ====================
from feature_utils import fix_suspicious_numeric

numeric_cleaner = FunctionTransformer(fix_suspicious_numeric, feature_names_out="one-to-one")

# ==================== Preprocess ====================
# Numeric: clean -> KNN impute -> scale
numeric_pipe = Pipeline(steps=[
    ("clean", numeric_cleaner),
    ("imputer", KNNImputer(n_neighbors=5)),
    ("scaler", StandardScaler())
])

# Categorical: impute -> one-hot
cat_pipe = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(drop="first", handle_unknown="ignore"))
])

preprocess = ColumnTransformer(
    transformers=[
        ("num", numeric_pipe, NUM_COL),
        ("cat", cat_pipe, CAT_COL),
    ],
    remainder="drop"
)

# ==================== Models ====================
models = []

models.append(("new_LogisticRegression", LogisticRegression(max_iter=5000, random_state=RANDOM_STATE)))
models.append(("new_RandomForest", RandomForestClassifier(random_state=RANDOM_STATE)))
models.append(("new_GradientBoosting", GradientBoostingClassifier(random_state=RANDOM_STATE)))
models.append(("new_HistGradientBoosting", HistGradientBoostingClassifier(random_state=RANDOM_STATE)))
models.append(("new_SVC", SVC(probability=True, random_state=RANDOM_STATE)))
models.append(("new_KNN", KNeighborsClassifier()))



models.append(("new_CatBoost", CatBoostClassifier(verbose=False, random_state=RANDOM_STATE)))


# ==================== CV Evaluate ====================
cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=RANDOM_STATE)

results = []
pipelines = {}

for name, clf in models:
    pipe = Pipeline(steps=[
        ("preprocess", preprocess),
        ("model", clf)
    ])
    pipelines[name] = pipe

    r = cross_validate(
        pipe,
        X_train_raw,
        y_train,
        cv=cv,
        scoring=["accuracy", "roc_auc"],
        return_train_score=True,
        n_jobs=-1
    )

    results.append({
        "name": name,
        "train_accuracy": float(np.mean(r["train_accuracy"])),
        "test_accuracy": float(np.mean(r["test_accuracy"])),
        "train_roc_auc": float(np.mean(r["train_roc_auc"])),
        "test_roc_auc": float(np.mean(r["test_roc_auc"])),
    })

results_df = pd.DataFrame(results).sort_values("test_roc_auc", ascending=False).reset_index(drop=True)
print("\n==================== CV Results (sorted by test ROC-AUC) ====================")
print(results_df.to_string(index=False))

# ==================== Pick Top-3 and Predict ====================
top_df = results_df.head(TOP_K).copy()
print(f"\n==================== Top {TOP_K} Models ====================")
print(top_df[["name", "test_accuracy", "test_roc_auc"]].to_string(index=False))

top_names = top_df["name"].tolist()
proba_list = []
for name in top_names:
    print(f"\nTraining full data and predicting test for: {name}")
    pipe = pipelines[name]
    pipe.fit(X_train_raw, y_train)
    joblib.dump(pipe, f"{name}.pkl")
    print(f"Saved model: {name}.pkl")
    pred = pipe.predict(X_test_raw)
    if hasattr(pipe, "predict_proba"):
        proba = pipe.predict_proba(X_test_raw)
        proba_list.append(proba[:, 1] if proba.shape[1] >= 2 else proba[:, 0])

    sub = pd.DataFrame({
        "id": np.arange(len(pred), dtype=int),
        "HeartDisease": pred.astype(int)
    })

    out_path = f"{name}_submission.csv"   # already has "new_" prefix in name
    sub.to_csv(out_path, index=False)
    print(f"Saved: {out_path}")

# ==================== Ensemble mean proba (top-3) ====================
if proba_list:
    mean_proba = np.mean(np.stack(proba_list, axis=0), axis=0)
    pred_mean = (mean_proba >= 0.5).astype(int)
    sub_mean = pd.DataFrame({
        "id": np.arange(len(pred_mean), dtype=int),
        "HeartDisease": pred_mean.astype(int)
    })
    out_path = "new_ensemble_mean_proba_submission.csv"
    sub_mean.to_csv(out_path, index=False)
    print(f"Saved: {out_path}")
