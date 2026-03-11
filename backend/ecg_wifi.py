import csv
import math
from collections import deque
import lttbc
import matplotlib.pyplot as plt
import numpy as np
import os
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from matplotlib.animation import FuncAnimation

import database
import pan_tompkins_plus_plus.address_features as af
from AF_detection import AFCVDetector

# --- Flask App Reference (set by backend_main.py) ---
flask_app = None

# --- Configuration ---
ESP32_IP = '192.168.56.1'
PORT = 80
WINDOW_SECONDS = 10  # How many seconds to show on the live graph
SAVE_DATA = False
# Reconnection settings
RECONNECT_DELAY = 2  # seconds to wait before reconnecting
MAX_RECONNECT_ATTEMPTS = 10  # 0 for infinite attempts
CONNECTION_TIMEOUT = 5  # socket connection timeout
# CSV_PATH = "pan_tompkins_plus_plus/results_csv/window_features.csv"

# Data storage
all_times = []
all_values = []
temp_times = []
temp_values = []
last_ecg_chunk = []
last_temp_chunk = []
ecg_data_cache = []
now_ecg_ts_min = 0
now_ecg_data = {
    "file": "rest_ecg_data_",
    "fs_hz": 0.0,
    "max_hr": 0.0,
    "avg_hr": 0.0,
    "st_label": "Up",
    "oldpeak": 0.0,
    "resting_ecg": "ST",
    "calc_time": 0.0
}
mode = "rest_ecg_data_"
exec = ThreadPoolExecutor()
af_detector = AFCVDetector(fs_hz=160, window_beats=100, min_new_rr_for_update=10)
last_af_result = {
    "af_detected": False,
    "af_raw": False,
    "cv_rr": None,
    "beats_used": 0,
    "vote_positive": 0,
    "vote_total": 0,
}

# Connection state
client_socket = None
socket_file = None
connection_lost = False
reconnect_attempts = 0

# Thread-safe queue for WebSocket display (update() pushes, get_points_chunk() pops)
_ecg_ws_deque = deque()
_ecg_running_mean = None

def init():
    ax.set_xlim(0, WINDOW_SECONDS)
    ax.set_ylim(-2, 5) 
    return line,

def connect_to_esp32():
    global client_socket, socket_file, connection_lost, reconnect_attempts
    
    print(f"Connecting to {ESP32_IP}:{PORT}...")
    
    try:
        if client_socket:
            try:
                client_socket.close()
            except:
                pass
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(CONNECTION_TIMEOUT)
        client_socket.connect((ESP32_IP, PORT))
        socket_file = client_socket.makefile('r')
        
        connection_lost = False
        reconnect_attempts = 0
        print("Connection successful!")
        return True
        
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def reconnect():
    global connection_lost
    connection_lost = True
    
    print(f"Attempting to reconnect...")
    time.sleep(RECONNECT_DELAY)
    
    return connect_to_esp32()

def _has_nan(d: dict) -> bool:
    for v in d.values():
        if isinstance(v, float) and math.isnan(v):
            return True
    return False

def update_now_ecg(data: dict) -> None:
    global now_ecg_data, now_ecg_ts_min, ecg_data_cache, flask_app
    result = data.result()

    # Skip if calc_features returned NaN (too few R-peaks)
    if _has_nan(result):
        print(f"Skipping window with NaN values (insufficient R-peaks): "
              f"max_hr={result.get('max_hr')}, avg_hr={result.get('avg_hr')}")
        return

    now_ecg_data = result

    now_ts = time.time() // 60
    if now_ecg_ts_min != now_ts:
        if now_ecg_ts_min != 0 and flask_app is not None:
            with flask_app.app_context():
                try:
                    database.add_hr_record(heart_rate = sum(ecg_data_cache) / len(ecg_data_cache))
                except Exception as e:
                    print(f"Error saving HR record: {e}")
        now_ecg_ts_min = now_ts
        ecg_data_cache.clear()
    ecg_data_cache.append(now_ecg_data["avg_hr"])

    if flask_app is not None:
        with flask_app.app_context():
            try:
                database.add_window_feature(database.now_user_id, now_ecg_data)
            except Exception as e:
                print(f"Error saving window feature: {e}")

def update(frame):
    global last_ts, last_ecg_chunk, last_temp_chunk, mode, connection_lost, last_af_result
    
    if connection_lost:
        if not reconnect():
            return line,
    
    try:
        if socket_file is None:
            return line,
            
        line_data = socket_file.readline().strip()
        
        if not line_data and not connection_lost:
            try:
                client_socket.send(b'\n')
            except:
                print("Connection lost detected, preparing to reconnect...")
                connection_lost = True
                return line,
        
        if line_data:
            # format: time_us,isExercise,voltage
            parts = line_data.split(',')
            if len(parts) != 3:
                return line,
            
            try:
                t_us = int(parts[0])           # ESP32 timestamp in microseconds
                is_exercise = int(parts[1])    # 0 = REST, 1 = EXERCISE
                voltage_str = parts[2].strip() # voltage or "NaN"
            except ValueError:
                return line,
            
            # Determine new mode from isExercise flag
            new_mode = "exercise_ecg_data_" if is_exercise else "rest_ecg_data_"
            
            # If mode switched, flush current buffer with the previous mode
            # Only flush if enough samples for meaningful R-peak detection (>= 2s at 160Hz)
            MIN_FLUSH_SAMPLES = 320
            if new_mode != mode:
                if len(temp_values) >= MIN_FLUSH_SAMPLES:
                    print(f"Mode switched: {mode} -> {new_mode}, flushing {len(temp_values)} samples")
                    last_ecg_chunk = temp_values.copy()
                    last_temp_chunk = temp_times.copy()
                    ts = np.asarray(temp_times, dtype=float)
                    ecg = np.asarray(temp_values, dtype=float)
                    exec.submit(af.calc_features, ts, ecg, base=mode).add_done_callback(update_now_ecg)
                    last_af_result = af_detector.update(ecg)
                else:
                    print(f"Mode switched: {mode} -> {new_mode}, discarding {len(temp_values)} samples (too few)")
                temp_times.clear()
                temp_values.clear()
                last_ts = time.time()
            mode = new_mode
            
            # Skip lead-off samples
            if voltage_str == "NaN":
                return line,
            
            val = float(voltage_str)
            
            # Use ESP32 timestamp for precise relative time (seconds)
            now_timestamp = time.time()
            now = now_timestamp - start_timestamp

            if now_timestamp - last_ts >= WINDOW_SECONDS:
                last_ecg_chunk = temp_values.copy()
                last_temp_chunk = temp_times.copy()
                ts = np.asarray(temp_times, dtype=float)
                ecg = np.asarray(temp_values, dtype=float)
                exec.submit(af.calc_features, ts, ecg, base=mode).add_done_callback(update_now_ecg)
                last_af_result = af_detector.update(ecg)

                temp_times.clear()
                temp_values.clear()
                last_ts = now_timestamp
                # print(f"lec: {last_ecg_chunk}, ltc: {last_temp_chunk}")
            
            temp_times.append(now)
            temp_values.append(val)
            _ecg_ws_deque.append((now, val))
            
            if SAVE_DATA:
                # Save to permanent lists
                all_times.append(now)
                all_values.append(val)

                # Update plot data (showing only last WINDOW_SECONDS)
                plot_slice_t = all_times[0:] 
                plot_slice_v = all_values[0:]
                
                line.set_data(plot_slice_t, plot_slice_v)
            
                # Shift X-axis view
                if now > WINDOW_SECONDS:
                    ax.set_xlim(now - WINDOW_SECONDS, now)
    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError) as e:
        print(f"Connection error: {e}")
        connection_lost = True
    except Exception as e:
        print(f"Error updating data: {e}")
    return line,

def get_points_chunk() -> dict:
    global _ecg_running_mean
    # Drain the thread-safe deque — only new points since last call
    points = []
    while _ecg_ws_deque:
        try:
            points.append(_ecg_ws_deque.popleft())
        except IndexError:
            break
    if not points:
        return {"times": [], "values": []}
    times = [p[0] for p in points]
    values = [p[1] for p in points]
    # Running mean for stable centering across batches
    for v in values:
        if _ecg_running_mean is None:
            _ecg_running_mean = v
        else:
            _ecg_running_mean += (v - _ecg_running_mean) * 0.001
    centered = [v - _ecg_running_mean for v in values]
    return {"times": times, "values": centered}

def get_heart_rate() -> float:
    global now_ecg_data
    return now_ecg_data["avg_hr"]

def get_mode() -> str:
    global mode
    return "exercise" if "exercise" in mode else "rest"


def get_af_result() -> dict:
    return last_af_result

# --- Run ---
def main() -> None:
    global fig, ax, line, start_timestamp, last_ts

    # --- Setup Plot ---
    fig, ax = plt.subplots()
    line, = ax.plot([], [], lw=1.5, color='blue')
    ax.set_title("ECG Live Feed")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Voltage (V)")
    ax.grid(True)

    # --- Socket Connection ---
    while not connect_to_esp32():
        print(f"Connection refused, retrying...")
        time.sleep(RECONNECT_DELAY)

    start_timestamp = time.time()
    last_ts = start_timestamp

    # with open(CSV_PATH, "w") as f:
    #     f.write("file,fs_hz,max_hr,avg_hr,st_label,oldpeak,resting_ecg,calc_time\n")

    try:
        if SAVE_DATA:
            print("Recording... Close plot window or press Ctrl+C to save and exit.")
            ani = FuncAnimation(fig, update, init_func=init, blit=True, interval=1, cache_frame_data=False)
            plt.show()
        else:
            print("Press Ctrl+C to stop...")
            while True:
                update(None)
                time.sleep(0.01)
        # print("Recording... Close plot window or press Ctrl+C to save and exit.")
        # ani = FuncAnimation(fig, update, init_func=init, blit=True, interval=1, cache_frame_data=False)
        # plt.show()
    except KeyboardInterrupt:
        print("\nInterrupt received. Stopping...")
    finally:
        # --- Save  ---
        out_dir = "ECG_DATA/"
        os.makedirs(out_dir, exist_ok=True)
        filename = f"full_session_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(out_dir, filename)

        if all_times:
            print(f"Saving {len(all_times)} samples to {filename}...")
            with open(filepath, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['relative_time_sec', 'ecg_value'])
                # zip pairs the time and value lists together for saving
                writer.writerows(zip(all_times, all_values))
            print("Save complete.")
        else:
            print("No data was recorded.")

        if client_socket:
            try:
                client_socket.close()
            except:
                pass
        if socket_file:
            try:
                socket_file.close()
            except:
                pass

if __name__ == "__main__":
    main()
