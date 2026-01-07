# predict_batch.py
import pandas as pd
from save_model import HeartDiseasePredictor

# ==========================================
# 1. 設定病人的「固定」基本資料
# (模型需要這些欄位才能運作，請根據實際情況修改)
# ==========================================
base_patient_info = {
    'Age': 21,              # 年齡
    'Sex': 'F',             # 性別
    'ChestPainType': 'NAP', # 胸痛類型 (ASY, NAP, ATA, TA)
    'ExerciseAngina': 'N'   # 運動是否有心絞痛 (Y/N)
}

# ==========================================
# 2. 輸入你的 12 組動態數據
# (已根據你的 Log 填入，Oldpeak 強制設為 0.012)
# ==========================================
ecg_chunks = [
    {'chunk_id': 1,  'MaxHR': 143.3, 'ST_Slope': 'Flat'},
    {'chunk_id': 2,  'MaxHR': 111.6, 'ST_Slope': 'Flat'},
    {'chunk_id': 3,  'MaxHR': 115.7, 'ST_Slope': 'Flat'},
    {'chunk_id': 4,  'MaxHR': 145.5, 'ST_Slope': 'Up'},
    {'chunk_id': 5,  'MaxHR': 118.5, 'ST_Slope': 'Up'},
    {'chunk_id': 6,  'MaxHR': 126.3, 'ST_Slope': 'Up'},
    {'chunk_id': 7,  'MaxHR': 131.5, 'ST_Slope': 'Up'},
    {'chunk_id': 8,  'MaxHR': 181.1, 'ST_Slope': 'Up'},
    {'chunk_id': 9, 'MaxHR': 177.8, 'ST_Slope': 'Up'},
    {'chunk_id': 10, 'MaxHR': 124.7, 'ST_Slope': 'Up'},
]

# ==========================================
# 3. 載入模型 (這裡用表現最好的 Gradient Boosting)
# ==========================================
predictor = HeartDiseasePredictor()
try:
    predictor.load_model('gradient_boosting_best.pkl')
    print(f"成功載入模型: {predictor.model_name}")
except:
    print("找不到模型檔案，請確認 .pkl 檔案存在")
    exit()

# ==========================================
# 4. 批量預測
# ==========================================
print("\n正在計算 12 個片段的風險趨勢...\n")

results_list = []

for chunk in ecg_chunks:
    # 1. 複製基本資料
    data = base_patient_info.copy()
    
    # 2. 填入該片段的動態資料
    data['MaxHR'] = chunk['MaxHR']
    data['ST_Slope'] = chunk['ST_Slope']
    
    # 3. 強制覆寫 Oldpeak 為 0.012 (依照你的要求)
    data['Oldpeak'] = -0.09 
    
    # 4. 進行預測
    pred_result = predictor.predict_detail(data)
    
    # 5. 整理結果
    results_list.append({
        'Chunk': chunk['chunk_id'],
        'MaxHR': f"{chunk['MaxHR']:.1f}",
        'ST_Slope': chunk['ST_Slope'],
        'Oldpeak': data['Oldpeak'],
        'Risk': pred_result['risk_level'],
        'Prob': pred_result['risk_percentage'] # 你的模型會回傳 "xx.x%"
    })

# ==========================================
# 5. 顯示漂亮表格
# ==========================================
df_results = pd.DataFrame(results_list)

# 設定顯示格式
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.colheader_justify', 'center')

print(df_results.to_string(index=False))

# 簡單趨勢分析
print("\n" + "="*50)
print("【分析報告】")
high_risk_chunks = df_results[df_results['Risk'] == '高風險']
if not high_risk_chunks.empty:
    print(f"⚠️ 警告：在第 {high_risk_chunks['Chunk'].tolist()} 片段偵測到高風險訊號！")
else:
    print("✅ 全部片段皆為低風險。")
    print("雖然前 3 個片段 ST_Slope 為 Flat (潛在危險)，但可能因 Oldpeak 低或 MaxHR 正常而被判定安全。")