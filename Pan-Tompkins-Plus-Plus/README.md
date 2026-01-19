# Pan-Tompkins++

## Script Notes 
- `address_features.py`: read `ECG_DATA/*.csv`, run R-peak + ST feature extraction, and append per-window features to `results_csv/window_features.csv`.
- `collect_features.py`: aggregate `window_features.csv` into rest/exercise summary stats, then write `results_csv/collectd_features.csv` and model input `results_csv/model_input_features.csv`.
- `predict.py`: load `results_csv/model_input_features.csv`, align features, run the three saved models, and output predictions to `results_csv/predictions_models.csv` and `results_csv/prediction_ensemble.json`.

把ECG資料存到 ECG_DATA資料夾裡面




