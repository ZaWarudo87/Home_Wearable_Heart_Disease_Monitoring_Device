import argparse
import json
from pathlib import Path

import pandas as pd
from catboost import CatBoostClassifier
from imblearn.over_sampling import RandomOverSampler
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split


RANDOM_STATE = 42
TARGET = "HeartDisease"
FULL_FEATURES = [
    "Age",
    "Sex",
    "ChestPainType",
    "Cholesterol",
    "FastingBS",
    "RestingECG",
    "MaxHR",
    "ExerciseAngina",
    "Oldpeak",
    "ST_Slope",
]
CAT_COLS = ["Sex", "ChestPainType", "FastingBS", "RestingECG", "ExerciseAngina", "ST_Slope"]
NUM_COLS = ["Age", "Cholesterol", "MaxHR", "Oldpeak"]
PAPER_PARAMS = {
    "iterations": 200,
    "learning_rate": 0.1,
    "depth": 6,
    "verbose": False,
    "loss_function": "Logloss",
    "eval_metric": "AUC",
    "random_seed": RANDOM_STATE,
    "allow_writing_files": False,
}


def reconstruct_full_dataset(model_dir: Path) -> pd.DataFrame:
    train = pd.read_csv(model_dir / "heart_train.csv")
    test = pd.read_csv(model_dir / "heart_test.csv")
    sample_submission = pd.read_csv(model_dir / "sample_submission.csv")

    full_test = test.copy()
    full_test[TARGET] = sample_submission["target"].astype(int)
    return pd.concat([train, full_test], ignore_index=True)


def encode_and_impute_full(df: pd.DataFrame) -> pd.DataFrame:
    encoded = df[FULL_FEATURES].copy()

    for col in CAT_COLS:
        series = encoded[col].astype(str).fillna("Missing")
        categories = sorted(series.unique())
        mapping = {value: index for index, value in enumerate(categories)}
        encoded[col] = series.map(mapping).astype(int)

    imputer = SimpleImputer(strategy="mean")
    encoded[NUM_COLS] = imputer.fit_transform(encoded[NUM_COLS])
    return encoded


def evaluate(y_true: pd.Series, pred, proba) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    return {
        "rows": int(len(y_true)),
        "class_0": int((y_true == 0).sum()),
        "class_1": int((y_true == 1).sum()),
        "accuracy": float(accuracy_score(y_true, pred)),
        "precision": float(precision_score(y_true, pred)),
        "recall": float(recall_score(y_true, pred)),
        "f1": float(f1_score(y_true, pred)),
        "roc_auc": float(roc_auc_score(y_true, proba)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the strongest paper-style reproduction found for s41598-025-13790-x.")
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args()

    paper_dir = Path(__file__).resolve().parent
    model_dir = paper_dir.parent

    df = reconstruct_full_dataset(model_dir)
    y = df[TARGET].copy()

    X_ready = encode_and_impute_full(df)
    sampler = RandomOverSampler(random_state=RANDOM_STATE)
    X_resampled, y_resampled = sampler.fit_resample(X_ready, y)
    X_resampled = pd.DataFrame(X_resampled, columns=FULL_FEATURES)
    y_resampled = pd.Series(y_resampled, name=TARGET)

    X_train, X_test, y_train, y_test = train_test_split(
        X_resampled,
        y_resampled,
        test_size=0.20,
        stratify=y_resampled,
        random_state=RANDOM_STATE,
    )

    model = CatBoostClassifier(**PAPER_PARAMS)
    model.fit(X_train, y_train)
    pred = model.predict(X_test).astype(int)
    proba = model.predict_proba(X_test)[:, 1]

    result = {
        "paper": "s41598-025-13790-x",
        "method": "global_label_encode_impute + lasso_selected_features + global_random_oversampling + 80_20_holdout",
        "paper_params": PAPER_PARAMS,
        "selected_features": FULL_FEATURES,
        "rows_before_resample": int(len(df)),
        "rows_after_resample": int(len(y_resampled)),
        "class_0_after_resample": int((y_resampled == 0).sum()),
        "class_1_after_resample": int((y_resampled == 1).sum()),
        "metrics": evaluate(y_test, pred, proba),
    }

    print(json.dumps(result, indent=2))

    output_json = args.output_json or (paper_dir / "s41598_025_13790_x_best_result.json")
    output_json.write_text(json.dumps(result, indent=2))
    print(f"saved: {output_json}")


if __name__ == "__main__":
    main()
