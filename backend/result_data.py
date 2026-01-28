import pandas as pd

import pan_tompkins_plus_plus.collect_features as cf
import pan_tompkins_plus_plus.predict as predict

def parse_user_info(user_info: dict, df: pd.DataFrame) -> dict:
    cf.base_patient_info = user_info
    model_input_feature = cf.collect_features(df)
    print(model_input_feature)
    return model_input_feature

def get_health_risk(df: pd.DataFrame) -> dict:
    result = predict.predict(pd.DataFrame([cf.collect_features(df)]))
    return {
        "risk_score": result.get("ensemble", {}).get("final_prob", 0) * 100,
        "level": result.get("ensemble", {}).get("risk_text", "未知風險")
    }

if __name__ == '__main__':
    result = get_health_risk()
    print(result)