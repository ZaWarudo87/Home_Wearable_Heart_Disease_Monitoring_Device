import json
from pathlib import Path

import pandas as pd
from catboost import CatBoostClassifier
from imblearn.over_sampling import RandomOverSampler
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split


RANDOM_STATE = 42
TARGET = "HeartDisease"
TUNED_PARAMS = {
    "iterations": 600,
    "learning_rate": 0.1,
    "depth": 6,
    "l2_leaf_reg": 3,
    "verbose": False,
    "loss_function": "Logloss",
    "eval_metric": "AUC",
    "random_seed": RANDOM_STATE,
    "allow_writing_files": False,
}

MODEL_CONFIGS = {
    "catboost_10f": {
        "features": [
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
        ],
        "categorical": ["Sex", "ChestPainType", "FastingBS", "RestingECG", "ExerciseAngina", "ST_Slope"],
        "numeric": ["Age", "Cholesterol", "MaxHR", "Oldpeak"],
        "threshold": 0.20,
    },
    "catboost_8f": {
        "features": [
            "Age",
            "Sex",
            "ChestPainType",
            "MaxHR",
            "ExerciseAngina",
            "Oldpeak",
            "ST_Slope",
            "RestingECG",
        ],
        "categorical": ["Sex", "ChestPainType", "ExerciseAngina", "ST_Slope", "RestingECG"],
        "numeric": ["Age", "MaxHR", "Oldpeak"],
        "threshold": 0.13,
    },
}


def reconstruct_full_dataset(model_dir: Path) -> pd.DataFrame:
    train = pd.read_csv(model_dir / "heart_train.csv")
    test = pd.read_csv(model_dir / "heart_test.csv")
    sample_submission = pd.read_csv(model_dir / "sample_submission.csv")

    full_test = test.copy()
    full_test[TARGET] = sample_submission["target"].astype(int)
    return pd.concat([train, full_test], ignore_index=True)


def encode_and_impute(df: pd.DataFrame, features: list[str], categorical: list[str], numeric: list[str]) -> tuple[pd.DataFrame, dict, dict]:
    encoded = df[features].copy()
    category_maps: dict[str, dict[str, int]] = {}

    for col in categorical:
        series = encoded[col].astype(str).fillna("Missing")
        categories = sorted(series.unique())
        mapping = {value: index for index, value in enumerate(categories)}
        encoded[col] = series.map(mapping).astype(int)
        category_maps[col] = mapping

    imputer = SimpleImputer(strategy="mean")
    encoded[numeric] = imputer.fit_transform(encoded[numeric])
    imputer_stats = {col: float(stat) for col, stat in zip(numeric, imputer.statistics_)}
    return encoded, category_maps, imputer_stats


def evaluate(y_true: pd.Series, proba, threshold: float) -> dict:
    pred = (proba >= threshold).astype(int)
    return {
        "rows": int(len(y_true)),
        "class_0": int((y_true == 0).sum()),
        "class_1": int((y_true == 1).sum()),
        "accuracy": float(accuracy_score(y_true, pred)),
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, proba)),
        "threshold": float(threshold),
    }


def train_and_export(config_name: str, config: dict, df: pd.DataFrame, out_dir: Path) -> dict:
    X_ready, category_maps, imputer_stats = encode_and_impute(
        df,
        config["features"],
        config["categorical"],
        config["numeric"],
    )
    y = df[TARGET].copy()

    sampler = RandomOverSampler(random_state=RANDOM_STATE)
    X_resampled, y_resampled = sampler.fit_resample(X_ready, y)
    X_resampled = pd.DataFrame(X_resampled, columns=config["features"])
    y_resampled = pd.Series(y_resampled, name=TARGET)

    X_train, X_test, y_train, y_test = train_test_split(
        X_resampled,
        y_resampled,
        test_size=0.20,
        stratify=y_resampled,
        random_state=RANDOM_STATE,
    )

    eval_model = CatBoostClassifier(**TUNED_PARAMS)
    eval_model.fit(X_train, y_train)
    test_proba = eval_model.predict_proba(X_test)[:, 1]
    metrics = evaluate(y_test, test_proba, config["threshold"])

    final_model = CatBoostClassifier(**TUNED_PARAMS)
    final_model.fit(X_resampled, y_resampled)

    model_path = out_dir / f"{config_name}.cbm"
    final_model.save_model(str(model_path))

    return {
        "model_name": config_name,
        "model_path": model_path.name,
        "features": config["features"],
        "categorical_features": config["categorical"],
        "numeric_features": config["numeric"],
        "threshold": config["threshold"],
        "paper_params": TUNED_PARAMS,
        "rows_before_resample": int(len(df)),
        "rows_after_resample": int(len(y_resampled)),
        "category_maps": category_maps,
        "numeric_imputer_stats": imputer_stats,
        "holdout_metrics": metrics,
    }


def main() -> None:
    paper_dir = Path(__file__).resolve().parent
    model_dir = paper_dir.parent
    df = reconstruct_full_dataset(model_dir)

    export_summary = {
        "paper": "s41598-025-13790-x",
        "dataset": "reconstructed Kaggle heart disease dataset",
        "rows": int(len(df)),
        "exports": [],
    }

    for model_name, config in MODEL_CONFIGS.items():
        export_summary["exports"].append(train_and_export(model_name, config, df, paper_dir))

    summary_path = paper_dir / "exported_models.json"
    summary_path.write_text(json.dumps(export_summary, indent=2))
    print(json.dumps(export_summary, indent=2))
    print(f"saved: {summary_path}")


if __name__ == "__main__":
    main()
