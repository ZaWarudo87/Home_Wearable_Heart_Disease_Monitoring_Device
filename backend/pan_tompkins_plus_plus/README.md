## Script Notes 
- `address_features.py`: read `ECG_DATA/*.csv`, run R-peak + ST feature extraction, and append per-window features to `results_csv/window_features.csv`.
- `collect_features.py`: aggregate `window_features.csv` into rest/exercise summary stats, then write `results_csv/collectd_features.csv` and model input `results_csv/model_input_features.csv`.
- `predict.py`: load `results_csv/model_input_features.csv`, apply the exported 8-feature CatBoost preprocessing from `model/exported_models.json`, run the saved CatBoost model, and output `results_csv/prediction_ensemble.json`.

把ECG資料存到 ECG_DATA資料夾裡面

## Raspberry Pi Requirements
- Needed for inference and feature extraction: `numpy`, `pandas`, `scipy`, `scikit-learn`, `joblib`, `catboost`, `peakutils`, `six`.
- Install example:
  - `pip install numpy pandas scipy scikit-learn joblib catboost peakutils six`



