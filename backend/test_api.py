"""
測試後端 API 的腳本
使用方法: python test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:5001"
TOKEN = "TEST_TOKEN_12345"

def test_google_auth():
    """測試 Google 登入"""
    print("\n=== 測試 Google 登入 ===")
    response = requests.post(
        f"{BASE_URL}/api/auth/google",
        json={"google_token": "fake_google_token_12345"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()

def test_auth_me():
    """測試獲取當前用戶資訊"""
    print("\n=== 測試獲取當前用戶資訊 ===")
    response = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_create_profile():
    """測試創建用戶資料"""
    print("\n=== 測試創建用戶資料 ===")
    profile_data = {
        "sex": "M",
        "age": 45,
        "chest_pain_type": "ATA",
        "exercise_angina": "N"
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/user/profile",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json=profile_data
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_submit_health_data():
    """測試提交健康數據"""
    print("\n=== 測試提交健康數據 ===")
    health_data = {
        "resting_bp": 120,
        "cholesterol": 200,
        "fasting_bs": 95
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/user/health-data",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json=health_data
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_get_health_data():
    """測試獲取健康數據歷史"""
    print("\n=== 測試獲取健康數據歷史 ===")
    response = requests.get(
        f"{BASE_URL}/api/v1/user/health-data",
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_health_summary():
    """測試獲取健康摘要"""
    print("\n=== 測試獲取健康摘要 ===")
    response = requests.get(
        f"{BASE_URL}/api/v1/health/summary",
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    print("開始測試後端 API...")
    print("請確保後端服務已啟動在 http://localhost:5001")
    
    try:
        # 測試流程
        test_google_auth()
        test_auth_me()
        test_create_profile()
        test_auth_me()  # 再次檢查用戶是否還是新用戶
        test_submit_health_data()
        test_get_health_data()
        test_health_summary()
        
        print("\n=== 所有測試完成 ===")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 無法連接到後端服務，請確保服務已啟動！")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
