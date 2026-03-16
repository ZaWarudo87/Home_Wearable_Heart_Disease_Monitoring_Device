## Script Notes 
- `address_features.py`: read `ECG_DATA/*.csv`, run R-peak + ST feature extraction, and append per-window features to `results_csv/window_features.csv`.
- `collect_features.py`: aggregate `window_features.csv` into rest/exercise summary stats, then write `results_csv/collectd_features.csv` and model input `results_csv/model_input_features.csv`.
- `predict.py`: load `results_csv/model_input_features.csv`, apply the exported 8-feature CatBoost preprocessing from `model/exported_models.json`, run the saved CatBoost model, and output `results_csv/prediction_ensemble.json`.

## Pan-Tompkins++ Source
- The R-peak detection logic in this folder is adapted from the public `Pan-Tompkins++` implementation released with:
  - Khan, N., and Imtiaz, M. N. (2022). `Pan-Tompkins++: A Robust Approach to Detect R-peaks in ECG Signals`. arXiv:2211.03171
- This project keeps the parts needed for ECG feature extraction and removes unused code for our deployment flow.

把ECG資料存到 ECG_DATA資料夾裡面

## Raspberry Pi Requirements
- Needed for inference and feature extraction: `numpy`, `pandas`, `scipy`, `scikit-learn`, `joblib`, `catboost`, `peakutils`, `six`.
- Install example:
  - `pip install numpy pandas scipy scikit-learn joblib catboost peakutils six`



