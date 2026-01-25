import json
import os
import pandas as pd
import subprocess
import sys

def parse_user_info(user_info: dict) -> dict:
    user_info_csv_path = "pan_tompkins_plus_plus/results_csv/model_input_features.csv"
    os.makedirs(os.path.dirname(user_info_csv_path), exist_ok=True)
    
    user_info["MaxHR"] = 0
    user_info["ST_Slope"] = "UP"
    user_info["Oldpeak"] = 0.0
    pd.DataFrame([user_info]).to_csv(user_info_csv_path, index=False, encoding="utf-8-sig")

    script_path = "pan_tompkins_plus_plus/collect_features.py"
    subprocess.run([sys.executable, script_path], check=True, text=True)

    updated_user_info_csv = pd.read_csv(user_info_csv_path)
    return_dict = {}
    # return_dict["id"] = int(updated_user_info_csv.iloc[0]["ID"])
    return_dict["max_hr"] = int(updated_user_info_csv.iloc[0]["MaxHR"])
    return_dict["oldpeak"] = float(updated_user_info_csv.iloc[0]["Oldpeak"])
    return_dict["st_slope"] = str(updated_user_info_csv.iloc[0]["ST_Slope"])
    return return_dict

def update_data() -> dict:
    script_path = "pan_tompkins_plus_plus/predict.py"
    subprocess.run([sys.executable, script_path], check=True, text=True)
        
    json_path = "pan_tompkins_plus_plus/results_csv/prediction_ensemble.json"
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