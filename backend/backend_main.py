# eventlet imports and monkey patching must be done before other imports
import eventlet
import eventlet.wsgi
eventlet.monkey_patch()

import json
import os
import random
import threading
import time
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, abort, send_from_directory
from flask_cors import CORS
from flask_sock import Sock
from simple_websocket import Server

import database
import gemini
import login
import pseudo_data

app = Flask(__name__)
CORS(app) 
sock = Sock(app)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
database.init_db(app)

# --- Frontend Server ---
# @app.route('/', methods=['GET'])
# def serve_index():
#     return send_from_directory('.', 'index.html')

# --- Authentication Endpoints ---
@app.route('/api/auth/google', methods=['POST'])
def auth_google():
    data = request.json
    google_token = data.get('google_token')
    
    if not google_token:
        abort(400, 'Missing google_token')
    print(f"Received Google Token (simulated verification): {google_token}...")
    return jsonify(pseudo_data.login(google_token))

@app.route('/api/auth/me', methods=['GET'])
def auth_me():
    user_data = pseudo_data.check_auth(request)

    if "error" in user_data:
        status_code, message = user_data["error"]
        abort(status_code, message)
        
    return jsonify({
        "is_new_user": not user_data["profile_completed"],
        "user": {
            "name": user_data["name"],
            "token": user_data["token"]
        }
    })

# --- User Profile and Health Data ---
@app.route('/api/v1/user/profile', methods=['POST'])
def create_user_profile():
    user_data = pseudo_data.check_auth(request)
    if "error" in user_data:
        status_code, message = user_data["error"]
        abort(status_code, message)
    data = request.json
    
    required_fields = ['sex', 'age', 'chest_pain_type', 'exercise_angina']
    for field in required_fields:
        if field not in data:
            abort(400, f'Missing required field: {field}')
    
    profile_data = {
        "sex": data["sex"],
        "age": data["age"],
        "chest_pain_type": data["chest_pain_type"],
        "exercise_angina": data["exercise_angina"]
    }
    return jsonify(database.update_userdata(user_data["id"], profile_data))

@app.route('/api/v1/user/health-data', methods=['POST'])
def submit_health_data():
    user_data = pseudo_data.check_auth(request)
    if "error" in user_data:
        status_code, message = user_data["error"]
        abort(status_code, message)
    data = request.json
    
    required_fields = ['resting_bp', 'cholesterol', 'fasting_bs']
    for field in required_fields:
        if field not in data:
            abort(400, f'Missing required field: {field}')
    
    result = database.add_health_record(user_data["id"], {
        "resting_bp": data["resting_bp"],
        "cholesterol": data["cholesterol"],
        "fasting_bs": data["fasting_bs"]
    })
    return jsonify(result)

@app.route('/api/v1/user/health-data', methods=['GET'])
def get_health_data():
    user_data = pseudo_data.check_auth(request)
    if "error" in user_data:
        status_code, message = user_data["error"]
        abort(status_code, message)
    return jsonify(database.get_health_data(user_data["id"]))

# --- Health Data API ---
@app.route('/api/v1/health/summary', methods=['GET'])
def get_health_summary():
    user_data = pseudo_data.check_auth(request)
    if "error" in user_data:
        status_code, message = user_data["error"]
        abort(status_code, message)
    return jsonify(database.get_health_summary(user_data["id"]))

@app.route('/api/v1/health/risk', methods=['GET'])
def get_health_risk():
    user_data = pseudo_data.check_auth(request)
    if "error" in user_data:
        status_code, message = user_data["error"]
        abort(status_code, message)
    return jsonify(pseudo_data.get_health_risk(user_data))

@app.route('/api/v1/charts/bp', methods=['GET'])
def get_chart_bp():
    user_data = pseudo_data.check_auth(request)
    if "error" in user_data:
        status_code, message = user_data["error"]
        abort(status_code, message)
    period = request.args.get('period', '7d')
    
    # To prevent others play our API
    if period == '7d':
        data = database.get_chart_data(user_data["id"], 7, 'bp')
        data["labels"] = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
        data["labels"].reverse()
    else: # 30d
        data = database.get_chart_data(user_data["id"], 30, 'bp')
        data["labels"] = [(datetime.now() - timedelta(days=i)).strftime('%m-%d') for i in range(30)]
        data["labels"].reverse()
    return jsonify(data)

@app.route('/api/v1/charts/hr', methods=['GET'])
def get_chart_hr():
    user_data = pseudo_data.check_auth(request)
    if "error" in user_data:
        status_code, message = user_data["error"]
        abort(status_code, message)
    interval = request.args.get('interval')
    period = request.args.get('period')
    
    if period == '1h':
        data = database.get_chart_data(user_data["id"], 60, 'hr')
    elif period == '6h':
        data = database.get_chart_data(user_data["id"], 360, 'hr')
    elif period == '24h':
        data = database.get_chart_data(user_data["id"], 48, 'hr')
    else: # 7d
        data = database.get_chart_data(user_data["id"], 336, 'hr')
    return jsonify(data)

# --- Real-time ECG WebSocket ---
def send_ecg_data(ws: Server):
    try:
        while True:
            points_chunk = pseudo_data.get_points_chunk()  # Keep using pseudo_data for ECG simulation
            message = json.dumps({"points": points_chunk})
            ws.send(message)
            time.sleep(0.16)
    except Exception as e:
        print(f"WebSocket send error or client disconnected: {e}")
    finally:
        print("ECG stream thread stopped.")

@sock.route('/ws/ecg/stream')
def ecg_stream(ws: Server):
    token = request.args.get('token')
    if not pseudo_data.check_auth_ws(token):
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


# --- Main ---
if __name__ == '__main__':
    print("Starting server with eventlet on http://localhost:39244") # dec(39244) = oct(114514)
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 39244)), app)

