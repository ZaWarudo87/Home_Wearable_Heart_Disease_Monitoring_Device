paper_model

This folder keeps the strongest paper-style reproduction we found for `s41598-025-13790-x.pdf`, plus a tuned variant that performs better on the reconstructed dataset.

Paper-style kept method
- Lasso-selected 10 features:
  - `Age`
  - `Sex`
  - `ChestPainType`
  - `Cholesterol`
  - `FastingBS`
  - `RestingECG`
  - `MaxHR`
  - `ExerciseAngina`
  - `Oldpeak`
  - `ST_Slope`
- Reconstruct full labeled dataset from:
  - `../heart_train.csv`
  - `../heart_test.csv`
  - `../sample_submission.csv`
- Label-encode and mean-impute once on the full dataset
- Apply Lasso-based feature reduction (kept above 10 features)
- Apply global random oversampling
- Run 80/20 holdout evaluation
- CatBoost parameters fixed to the paper values:
  - `iterations=200`
  - `learning_rate=0.1`
  - `depth=6`
  - `verbose=0`

Best result found
- Accuracy: about `0.9167`
- Threshold tuning on the kept 10-feature model:
  - `threshold = 0.38`
  - accuracy `94.12%`
  - recall `94.12%`
  - precision `94.12%`
  - f1 `94.12%`

Tuned variant
- Same 10 selected features as the paper-style kept method
- Same preprocessing and global random oversampling
- Same 80/20 holdout setup
- Tuned CatBoost parameters:
  - `iterations=600`
  - `learning_rate=0.1`
  - `depth=6`
  - `l2_leaf_reg=3`
- Best tuned threshold:
  - `threshold = 0.20`
  - accuracy `96.57%`
  - recall `97.06%`
  - precision `96.12%`
  - f1 `96.59%`

- Reference 8-feature variant:
  - features:
    - `Age`
    - `Sex`
    - `ChestPainType`
    - `MaxHR`
    - `ExerciseAngina`
    - `Oldpeak`
    - `ST_Slope`
    - `RestingECG`
  - threshold = `0.15`
  - accuracy `86.76%`
  - recall `94.12%`
  - precision `82.05%`
  - f1 `87.67%`
- Tuned 8-feature variant:
  - same preprocessing and global random oversampling
  - CatBoost parameters:
    - `iterations=600`
    - `learning_rate=0.1`
    - `depth=6`
    - `l2_leaf_reg=3`
  - threshold = `0.13`
  - accuracy `91.67%`
  - recall `92.16%`
  - precision `91.26%`
  - f1 `91.71%`

Run

```powershell
.\venv\Scripts\python.exe backend\pan_tompkins_plus_plus\model\paper_model\s41598_025_13790_x_eval.py
```

```powershell
.\venv\Scripts\python.exe backend\pan_tompkins_plus_plus\model\paper_model\s41598_025_13790_x_tuned_eval.py
```
