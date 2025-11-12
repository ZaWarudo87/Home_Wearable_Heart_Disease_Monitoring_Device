# --- ADDED: Eventlet Imports & Monkey Patching ---
# 必須放在所有其他 import 之前
import eventlet
import eventlet.wsgi
eventlet.monkey_patch()
# --- END ADDED ---

import time
import json
import random
import threading
from datetime import datetime, timedelta

# 'request' 已經在
from flask import Flask, request, jsonify, abort, send_from_directory
from flask_cors import CORS
from flask_sock import Sock

# --- Flask App Setup ---
app = Flask(__name__)
# 允許所有來源的 CORS (測試用)
CORS(app) 
# 初始化 WebSocket
sock = Sock(app)

# --- 假資料庫和輔助函數 ---

# 模擬一個有效的使用者 API 權杖
VALID_API_TOKEN = "TEST_TOKEN_12345"

# 模擬用戶資料庫（實際應用中應使用真實資料庫）
user_database = {}

# 模擬 PQRST 波 (來自您之前的需求)
ONE_HEARTBEAT = [
    0, 0.05, 0.1, 0.05, 0, 0, -0.1, -0.2, 1.5, -0.8, 0.1, 0, 
    0, 0.1, 0.2, 0.25, 0.2, 0.1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
]

# --- FIXED: 恢復函數內容 ---
def generate_chart_data(points, type='hr'):
    """生成圖表標籤和隨機值"""
    labels = [(datetime.now() - timedelta(minutes=i)).strftime('%H:%M') for i in range(points)]
    labels.reverse()
    if type == 'hr':
        values = [random.randint(60, 90) for _ in range(points)]
    else:
        values = [random.randint(110, 130) for _ in range(points)]
    return {"labels": labels, "values": values}

# --- FIXED: 恢復函數內容 ---
def check_auth(request):
    """檢查請求中是否有有效的 Authorization 標頭"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        abort(401, 'Missing Authorization Header')
    
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != 'bearer' or token != VALID_API_TOKEN:
            abort(401, 'Invalid Token')
    except ValueError:
        abort(401, 'Invalid Authorization Header')
    # 驗證通過
    print("Auth check passed")

# --- ADDED: Serve index.html at the root ---

# @app.route('/', methods=['GET'])
# def serve_index():
# # --- FIXED: 恢復函數內容 ---
#     """
#     在根路由 (/) 提供 index.html 檔案。
#     '.' 表示當前目錄 (與 main.py 相同的目錄)
#     """
#     return send_from_directory('.', 'index.html')


# --- 1. Authentication Endpoints ---

@app.route('/api/auth/google', methods=['POST'])
def auth_google():
# --- FIXED: 恢復函數內容 ---
    """模擬 Google 登入"""
    data = request.json
    google_token = data.get('google_token')
    
    if not google_token:
        abort(400, 'Missing google_token')
        
    print(f"Received Google Token (simulated verification): {google_token[:20]}...")
    
    # 模擬從 Google token 中提取用戶 email（實際應用中應解析真實的 JWT）
    user_email = "test.user@google.com"
    
    # 檢查是否為新用戶
    is_new_user = user_email not in user_database
    
    if is_new_user:
        # 創建新用戶記錄
        user_database[user_email] = {
            "email": user_email,
            "name": "王小明 (來自後端)",
            "profile_completed": False,
            "profile_data": None,
            "health_data": []
        }
    
    # 假設驗證成功
    return jsonify({
        "api_token": VALID_API_TOKEN,
        "is_new_user": is_new_user,
        "user": {
            "name": user_database[user_email]["name"],
            "email": user_email
        }
    })

@app.route('/api/auth/me', methods=['GET'])
def auth_me():
# --- FIXED: 恢復函數內容 ---
    """獲取當前使用者資訊 (用於頁面刷新)"""
    check_auth(request) # 驗證 Token
    
    # 模擬用戶 email（實際應用中應從 token 中提取）
    user_email = "test.user@google.com"
    
    if user_email not in user_database:
        user_database[user_email] = {
            "email": user_email,
            "name": "王小明 (來自後端)",
            "profile_completed": False,
            "profile_data": None,
            "health_data": []
        }
    
    user_data = user_database[user_email]
    
    return jsonify({
        "is_new_user": not user_data["profile_completed"],
        "user": {
            "name": user_data["name"],
            "email": user_email
        }
    })

# --- 3. User Profile and Health Data Endpoints ---

@app.route('/api/v1/user/profile', methods=['POST'])
def create_user_profile():
    """創建或更新用戶基本資料"""
    check_auth(request)
    data = request.json
    
    # 驗證必要欄位
    required_fields = ['sex', 'age', 'chest_pain_type', 'exercise_angina']
    for field in required_fields:
        if field not in data:
            abort(400, f'Missing required field: {field}')
    
    # 模擬用戶 email
    user_email = "test.user@google.com"
    
    if user_email not in user_database:
        abort(404, 'User not found')
    
    # 更新用戶資料
    user_database[user_email]["profile_data"] = {
        "sex": data["sex"],
        "age": data["age"],
        "chest_pain_type": data["chest_pain_type"],
        "exercise_angina": data["exercise_angina"],
        "created_at": datetime.now().isoformat()
    }
    user_database[user_email]["profile_completed"] = True
    
    print(f"User profile created/updated: {user_database[user_email]['profile_data']}")
    
    return jsonify({
        "message": "Profile created successfully",
        "profile": user_database[user_email]["profile_data"]
    })

@app.route('/api/v1/user/health-data', methods=['POST'])
def submit_health_data():
    """提交健康數據"""
    check_auth(request)
    data = request.json
    
    # 驗證必要欄位
    required_fields = ['resting_bp', 'cholesterol', 'fasting_bs']
    for field in required_fields:
        if field not in data:
            abort(400, f'Missing required field: {field}')
    
    # 模擬用戶 email
    user_email = "test.user@google.com"
    
    if user_email not in user_database:
        abort(404, 'User not found')
    
    # 添加健康數據記錄
    health_record = {
        "resting_bp": data["resting_bp"],
        "cholesterol": data["cholesterol"],
        "fasting_bs": data["fasting_bs"],
        "timestamp": datetime.now().isoformat()
    }
    
    user_database[user_email]["health_data"].append(health_record)
    
    print(f"Health data submitted: {health_record}")
    
    return jsonify({
        "message": "Health data submitted successfully",
        "data": health_record
    })

@app.route('/api/v1/user/health-data', methods=['GET'])
def get_health_data():
    """獲取用戶的健康數據歷史"""
    check_auth(request)
    
    user_email = "test.user@google.com"
    
    if user_email not in user_database:
        abort(404, 'User not found')
    
    return jsonify({
        "health_data": user_database[user_email]["health_data"]
    })

# --- 4. Health Data REST API Endpoints ---

@app.route('/api/v1/health/summary', methods=['GET'])
def get_health_summary():
# --- FIXED: 恢復函數內容 ---
    check_auth(request)
    return jsonify({
      "last_update": datetime.now().isoformat(),
      "overview": {
        "resting_bp": random.randint(115, 125),
        "avg_hr": random.randint(70, 80),
        "max_hr": random.randint(150, 160),
        "oldpeak": round(random.uniform(0.5, 1.2), 1)
      },
      "ai_summary": "這是來自 Python 後端的 AI 健康建議。請保持規律運動並監測您的心率。"
    })

@app.route('/api/v1/health/risk', methods=['GET'])
def get_health_risk():
# --- FIXED: 恢復函數內容 ---
    check_auth(request)
    return jsonify({
      "risk_score": random.randint(30, 40),
      "level": "低風險 (來自後端)"
    })

@app.route('/api/v1/charts/bp', methods=['GET'])
def get_chart_bp():
# --- FIXED: 恢復函數內容 ---
    check_auth(request)
    period = request.args.get('period', '7d')
    
    if period == '7d':
        data = generate_chart_data(7, 'bp')
        data["labels"] = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
        data["labels"].reverse()
    else: # 30d
        data = generate_chart_data(30, 'bp')
        data["labels"] = [(datetime.now() - timedelta(days=i)).strftime('%m-%d') for i in range(30)]
        data["labels"].reverse()
        
    return jsonify(data)

@app.route('/api/v1/charts/hr', methods=['GET'])
def get_chart_hr():
# --- FIXED: 恢復函數內容 ---
    check_auth(request)
    interval = request.args.get('interval')
    period = request.args.get('period')
    
    # 根據參數決定生成多少數據點 (簡化模擬)
    if period == '1h':
        data = generate_chart_data(60, 'hr')
    elif period == '6h':
        data = generate_chart_data(360, 'hr')
    elif period == '24h':
        data = generate_chart_data(48, 'hr') # 30min interval
    else: # 7d
        data = generate_chart_data(336, 'hr') # 30min interval
        
    return jsonify(data)


# --- 5. Real-time ECG WebSocket Endpoint ---

def send_ecg_data(ws):
# ... (此函數內容本來就是完整的) ...
    index = 0
    try:
        while True:
            points_chunk = []
            for _ in range(20):
                noise = random.uniform(-0.05, 0.05)
                points_chunk.append(ONE_HEARTBEAT[index] + noise)
                index = (index + 1) % len(ONE_HEARTBEAT)
            
            message = json.dumps({"points": points_chunk})
            ws.send(message)
            
            time.sleep(0.16) 
            
    except Exception as e:
        print(f"WebSocket send error or client disconnected: {e}")
    finally:
        print("ECG stream thread stopped.")

@sock.route('/ws/ecg/stream')
def ecg_stream(ws):
# ... (此函數內容本來就是完整的) ...
    token = request.args.get('token')
    
    if not token or token != VALID_API_TOKEN:
        print(f"WebSocket connection rejected: Invalid token '{token}'")
        ws.close()
        return

    print(f"WebSocket connection accepted for token: {token}")
    
    thread = threading.Thread(target=send_ecg_data, args=(ws,))
    thread.daemon = True
    thread.start()

    try:
        thread.join()
        print("ECG stream function exiting after thread join.")
    except Exception as e:
        print(f"Exception while waiting for send_ecg_data thread: {e}")
    finally:
        print("Client disconnected.")


# --- Run the App ---
if __name__ == '__main__':
# ... (此函數內容本來就是完整的) ...
    print("Starting server with eventlet on http://localhost:5001")
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5001)), app)

