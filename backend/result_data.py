import json
import os
import pandas as pd
import subprocess
import sys

def parse_user_info(user_info: dict) -> dict:
    user_info_csv_path = os.path.join(os.path.dirname(__file__), '..', 'Pan-Tompkins-Plus-Plus', 'results_csv', 'model_input_features.csv')
    os.makedirs(os.path.dirname(user_info_csv_path), exist_ok=True)
    # if not os.path.exists(user_info_csv_path):
    #     # create parent dir if needed and write an empty CSV with header
    #     os.makedirs(os.path.dirname(user_info_csv_path), exist_ok=True)
    #     with open(user_info_csv_path, 'w', encoding='utf-8', newline='') as f:
    #         f.write("Age,Sex,ChestPainType,ExerciseAngina,RestingBP,Cholesterol,FastingBS,MaxHR,ST_Slope,Oldpeak\n")
    #         f.write("0,M,ASY,N,0,0,0,0,UP,0.0\n")
    # user_info_csv = pd.read_csv(user_info_csv_path)
    
    user_info["MaxHR"] = 0
    user_info["ST_Slope"] = "UP"
    user_info["Oldpeak"] = 0.0
    pd.DataFrame([user_info]).to_csv(user_info_csv_path, index=False, encoding="utf-8-sig")

    script_path = os.path.join(os.path.dirname(__file__), '..', 'Pan-Tompkins-Plus-Plus', 'collect_features.py')
    subprocess.run([sys.executable, script_path], check=True, text=True, cwd=os.path.dirname(script_path))

    updated_user_info_csv = pd.read_csv(user_info_csv_path)
    return_dict = {}
    return_dict["max_hr"] = int(updated_user_info_csv.iloc[0]["MaxHR"])
    return_dict["oldpeak"] = float(updated_user_info_csv.iloc[0]["Oldpeak"])
    return_dict["st_slope"] = str(updated_user_info_csv.iloc[0]["ST_Slope"])
    return return_dict

def update_data() -> dict:
    script_path = os.path.join(os.path.dirname(__file__), '..', 'Pan-Tompkins-Plus-Plus', 'predict.py')
    subprocess.run([sys.executable, script_path], check=True, text=True, cwd=os.path.dirname(script_path))
        
    json_path = os.path.join(os.path.dirname(__file__), '..', 'Pan-Tompkins-Plus-Plus', 'results_csv', 'prediction_ensemble.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def get_health_risk() -> dict:
    result = update_data()
    return {
        "risk_score": result.get("ensemble", {}).get("final_prob", 0) * 100,
        "level": result.get("ensemble", {}).get("risk_text", "未知風險")
    }

if __name__ == '__main__':
    result = update_data()
    print(result)