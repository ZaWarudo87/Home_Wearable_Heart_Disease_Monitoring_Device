from datetime import datetime, timedelta
from flask import request
import random

VALID_API_TOKEN = "TEST_TOKEN_12345"
user_database = {}
ONE_HEARTBEAT = [
    0, 0.05, 0.1, 0.05, 0, 0, -0.1, -0.2, 1.5, -0.8, 0.1, 0, 
    0, 0.1, 0.2, 0.25, 0.2, 0.1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
]

def get_chart_data(token: str, points: int, type: str ='hr') -> dict:
    if type == 'hr':
        if points > 360:
            points //= 1800
            labels = [(datetime.now() - timedelta(minutes=i * 1800)).strftime('%H:%M') for i in range(points)]
        else:
            labels = [(datetime.now() - timedelta(minutes=i)).strftime('%H:%M') for i in range(points)]
        values = [random.randint(60, 90) for _ in range(points)]
    else:
        labels = [(datetime.now() - timedelta(minutes=i)).strftime('%Y-%m-%d') for i in range(points)]
        values = [random.randint(110, 130) for _ in range(points)]
    labels.reverse()
    return {"labels": labels, "values": values}

def check_auth(request: request) -> dict:
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return {"error": (401, 'Missing Authorization Header')}
    
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != 'bearer' or token != VALID_API_TOKEN:
            return {"error": (401, 'Invalid Token')}
    except ValueError:
        return {"error": (401, 'Invalid Authorization Header')}
    
    return random.choice(list(user_database.values()))
    # print("Auth check passed")

def login(google_token: str) -> dict:
    user_token = f"{random.randint(1000,9999)}@gmail.com"
    is_new_user = user_token not in user_database
    
    if is_new_user:
        # 創建新用戶記錄
        # id starts from 1 and increments
        new_id = len(user_database) + 1
        user_database[user_token] = {
            "id": new_id,
            "token": user_token,
            "name": "王小明 (來自後端)",
            "profile_completed": False,
            "profile_data": None,
            "health_data": []
        }
        
    return {
        "api_token": VALID_API_TOKEN,
        "is_new_user": is_new_user,
        "user": {
            "name": user_database[user_token]["name"],
            "token": user_token
        }
    }

def update_userdata(token: str, data: dict) -> dict:
    if token in user_database:
        user_database[token].update(data)
        # print(f"User data updated for {token}: {data}")
        return {"message": "User data updated successfully"}
    else:
        return {"error": "User not found"}
    
def get_health_summary(user_data: dict) -> dict:
    last_update = datetime.now().isoformat()
    overview = {
        "resting_bp": random.randint(115, 125),
        "avg_hr": random.randint(70, 80),
        "max_hr": random.randint(150, 160),
        "oldpeak": round(random.uniform(0.5, 1.2), 1)
    }
    return {
        "last_update": last_update,
        "overview": overview,
        "ai_summary": "這是來自 Python 後端的 AI 健康建議。請保持規律運動並監測您的心率。"
    }
    
def get_health_risk() -> dict:
    return {
        "risk_score": random.randint(30, 40),
        "level": "低風險"
    }

def get_points_chunk(index: int = 0, chunk_size: int = 20) -> list:
    points_chunk = []
    for _ in range(chunk_size):
        noise = random.uniform(-0.05, 0.05)
        points_chunk.append(ONE_HEARTBEAT[index] + noise)
        index = (index + 1) % len(ONE_HEARTBEAT)
    return points_chunk

def get_heart_rate(ecg_points: list) -> int:
    return random.randint(65, 70)

def check_auth_ws(token: str) -> bool:
    return token == VALID_API_TOKEN