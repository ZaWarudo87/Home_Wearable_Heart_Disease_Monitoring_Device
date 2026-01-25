# Libraries
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.impute import KNNImputer
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, cross_validate, StratifiedKFold
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, HistGradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

import warnings
warnings.filterwarnings("ignore")

# ==================== Data Review ====================
# Training
df_train = pd.read_csv("heart_train.csv")
df_test  = pd.read_csv("heart_test.csv")

# ==================== 選擇特定特徵 ====================
# 只保留: Age, Sex, MaxHR, Oldpeak, ST_Slope, HeartDisease (target)
selected_features = ['Age', 'Sex','ChestPainType', 'MaxHR', 'ExerciseAngina' ,'Oldpeak', 'ST_Slope','HeartDisease']
df_train_selected = df_train[selected_features].copy()

test_features = ['Age', 'Sex','ChestPainType', 'MaxHR', 'ExerciseAngina' ,'Oldpeak', 'ST_Slope']
df_test_selected = df_test[test_features].copy()

print("Training data shape:", df_train_selected.shape)
print("Testing data shape:", df_test_selected.shape)

# ==================== Feature Engineering ====================
# One-Hot Encoding
cat_col = ['Sex', 'ST_Slope', 'ChestPainType', 'ExerciseAngina']
num_col = ['Age', 'MaxHR', 'Oldpeak']

df_train_encoded = pd.get_dummies(data=df_train_selected, columns=cat_col, drop_first=True)
df_test_encoded = pd.get_dummies(data=df_test_selected, columns=cat_col, drop_first=True)

print("\nAfter encoding:")
print("Training columns:", df_train_encoded.columns.tolist())
print("Testing columns:", df_test_encoded.columns.tolist())

# ==================== Preprocessing Functions ====================
def suspicious_data(df):
    """處理可疑數據"""
    df = df.copy()
    
    
    # 使用 KNN imputation 填補缺失值
    if df.isnull().any().any():
        col = df.columns[df.isnull().any()].tolist()
        
        scaler = MinMaxScaler()
        scaled_values = scaler.fit_transform(df[col])
        
        imputer = KNNImputer()
        imputed_values = imputer.fit_transform(scaled_values)
        
        imputed_inverse = scaler.inverse_transform(imputed_values)
        
        df_imputed = pd.DataFrame(imputed_inverse, columns=col, index=df.index)
        df[col] = df_imputed[col]
    
    return df

def handle_outliers(df):
    """處理異常值"""
    df = df.copy()
    col = df.select_dtypes(include=['float', 'int']).columns
    
    for i in col:
        if i in df.columns:
            series = df[i]
            z_scores = stats.zscore(series)
            lower = series[z_scores > -3].min()
            upper = series[z_scores < 3].max()
            df[i] = series.clip(lower, upper)
    
    return df

def transformation(df, exclude_cols=None):
    """數據轉換 (排除目標變數)"""
    df = df.copy()
    
    if exclude_cols is None:
        exclude_cols = []
    
    # 選擇數值型欄位,但排除指定的欄位
    col = [c for c in df.select_dtypes(include=['float', 'int']).columns 
           if c not in exclude_cols]
    
    for i in col:
        if i in df.columns:
            if -1 < df[i].skew() < 1:
                std_scaler = StandardScaler()
                df[i] = std_scaler.fit_transform(df[[i]])
            else:
                minmax_scaler = MinMaxScaler()
                df[i] = minmax_scaler.fit_transform(df[[i]])
    
    return df

# ==================== ModelRunner Class ====================
class ModelRunner:
    def __init__(self, model, name=None, param_grid=None, search_type=None, n_iter=20):
        self.model = model
        self.name = name if name else type(model).__name__
        self.param_grid = param_grid
        self.search_type = search_type
        self.n_iter = n_iter
        self.best_model = None
        self.best_parameters = None

    def tune(self, X, y, cv=5, scoring="roc_auc"):
        if self.param_grid is None:
            self.model.fit(X, y)
            self.best_model = self.model
            self.searcher = None
            return self

        if self.search_type == "grid":
            searcher = GridSearchCV(self.model, self.param_grid, cv=cv, scoring=scoring, n_jobs=-1)
        elif self.search_type == "random":
            searcher = RandomizedSearchCV(self.model, self.param_grid, cv=cv, 
                                          scoring=scoring, n_jobs=-1, n_iter=self.n_iter,
                                          random_state=42)
        else:
            raise ValueError("search_type must be 'grid' or 'random' if param_grid is given")
        
        searcher.fit(X, y)
        self.best_model = searcher.best_estimator_
        self.best_parameters = searcher.best_params_
        self.searcher = searcher
        return self
    
    def evaluate(self, X, y, cv=10):
        model_to_eval = self.best_model if self.best_model else self.model
        r = cross_validate(model_to_eval, X, y, cv=cv,
                           scoring=['accuracy', 'roc_auc'],
                           return_train_score=True)        
        return {
            "name": self.name,
            "train_accuracy": r['train_accuracy'].mean(),
            "test_accuracy": r['test_accuracy'].mean(),
            "train_roc_auc": r['train_roc_auc'].mean(),
            "test_roc_auc": r['test_roc_auc'].mean()
        }

    def fit_predict(self, X_train, y_train, X_test):
        model_to_eval = self.best_model if self.best_model else self.model
        m = model_to_eval.fit(X_train, y_train)
        return m.predict(X_test)

# ==================== 準備訓練數據 ====================
# 處理訓練數據
df_train_processed = suspicious_data(df_train_encoded)
df_train_processed = handle_outliers(df_train_processed)

# 分離特徵和目標
X = df_train_processed.drop(['HeartDisease'], axis=1)
y = df_train_processed['HeartDisease']

# 處理測試數據
df_test_processed = suspicious_data(df_test_encoded)
df_test_processed = handle_outliers(df_test_processed)

print("\n處理後的訓練數據特徵:", X.columns.tolist())
print("訓練數據形狀:", X.shape)
print("測試數據形狀:", df_test_processed.shape)

# ==================== 模型訓練 ====================
print("\n========== 開始訓練不需要轉換的模型 ==========")

# 不需要數據轉換的模型
models = [
    ModelRunner(RandomForestClassifier(random_state=369), 'Random Forest'),
    ModelRunner(GradientBoostingClassifier(random_state=369), 'Gradient Boosting'),
    ModelRunner(HistGradientBoostingClassifier(random_state=369), 'HistGradient Boosting'),
    ModelRunner(XGBClassifier(random_state=369), 'XGBoost'),
    ModelRunner(LGBMClassifier(verbose=-1, random_state=369), 'LightGBM'),
    ModelRunner(CatBoostClassifier(verbose=False, random_state=369), 'CatBoost')
]

results_data = []
for m in models:
    print(f"\n訓練 {m.name}...")
    result = m.evaluate(X, y)
    results_data.append(result)
    print(f"{m.name} - Test Accuracy: {result['test_accuracy']:.4f}, Test ROC-AUC: {result['test_roc_auc']:.4f}")

# ==================== 需要轉換的模型 ====================
print("\n========== 開始訓練需要轉換的模型 ==========")

# 數據轉換 (排除目標變數 HeartDisease)
df_train_transformed = transformation(df_train_processed.copy(), exclude_cols=['HeartDisease'])
X_trans = df_train_transformed.drop(['HeartDisease'], axis=1)
y_trans = df_train_transformed['HeartDisease']

df_test_transformed = transformation(df_test_processed.copy())

# 需要數據轉換的模型
models_trans = [
    ModelRunner(LogisticRegression(max_iter=5000, random_state=369), 'Logistic Regression'),
    ModelRunner(KNeighborsClassifier(), 'KNN'),
    ModelRunner(SGDClassifier(random_state=369), 'SGDC'),
    ModelRunner(SVC(random_state=369), 'SVM')
]

for m in models_trans:
    print(f"\n訓練 {m.name}...")
    result = m.evaluate(X_trans, y_trans)
    results_data.append(result)
    print(f"{m.name} - Test Accuracy: {result['test_accuracy']:.4f}, Test ROC-AUC: {result['test_roc_auc']:.4f}")

# ==================== 結果匯總 ====================
results_df = pd.DataFrame(results_data)
results_df = results_df.sort_values('test_roc_auc', ascending=False)
print("\n" + "="*80)
print("最終結果 (按 Test ROC-AUC 排序):")
print("="*80)
print(results_df.to_string(index=False))

# ==================== 生成預測 ====================
print("\n========== 生成預測結果 ==========")

# 不需要轉換的模型預測
for m in models:
    print(f"生成 {m.name} 預測...")
    predictions = m.fit_predict(X, y, df_test_processed)
    sub = pd.DataFrame({"id": range(len(predictions)),
                        "HeartDisease": predictions})
    sub.to_csv(f"{m.name}_submission.csv", index=False)

# 需要轉換的模型預測
for m in models_trans:
    print(f"生成 {m.name} 預測...")
    predictions = m.fit_predict(X_trans, y_trans, df_test_transformed)
    sub = pd.DataFrame({"id": range(len(predictions)),
                        "HeartDisease": predictions})
    sub.to_csv(f"{m.name}_submission.csv", index=False)

print("\n所有預測文件已生成完畢!")