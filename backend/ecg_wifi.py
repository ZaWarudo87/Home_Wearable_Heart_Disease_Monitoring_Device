import csv
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

# --- Flask App Reference (set by backend_main.py) ---
flask_app = None

# --- Configuration ---
ESP32_IP = '127.0.0.1' 
PORT = 80
WINDOW_SECONDS = 10  # How many seconds to show on the live graph
SAVE_DATA = False

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
    "file": "-",
    "fs_hz": 0.0,
    "max_hr": 0.0,
    "avg_hr": 0.0,
    "st_label": "Up",
    "oldpeak": 0.0,
    "resting_ecg": "ST",
    "calc_time": 0.0
}
exec = ThreadPoolExecutor()

def init():
    ax.set_xlim(0, WINDOW_SECONDS)
    ax.set_ylim(-2, 5) 
    return line,

def update_now_ecg(data: dict) -> None:
    global now_ecg_data, now_ecg_ts_min, ecg_data_cache, flask_app
    now_ecg_data = data.result()

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

def update(frame):
    global last_ts, last_ecg_chunk, last_temp_chunk
    try:
        line_data = socket_file.readline().strip()
        if line_data:
            val = float(line_data)
            now_timestamp = time.time()
            now = now_timestamp - start_timestamp

            if now_timestamp - last_ts >= WINDOW_SECONDS:
                last_ecg_chunk = temp_values.copy()
                last_temp_chunk = temp_times.copy()
                ts = np.asarray(temp_times, dtype=float)
                ecg = np.asarray(temp_values, dtype=float)
                exec.submit(af.calc_features, ts, ecg).add_done_callback(update_now_ecg)

                temp_times.clear()
                temp_values.clear()
                last_ts = now_timestamp
            
            temp_times.append(now)
            temp_values.append(val)
            
            if SAVE_DATA:
                # Save to permanent lists
                all_times.append(now)
                all_values.append(val)

                # Update plot data (showing only last WINDOW_SECONDS)
                # slice the list [-500:] to keep the plot fast/responsive
                plot_slice_t = all_times[0:] 
                plot_slice_v = all_values[0:]
                
                line.set_data(plot_slice_t, plot_slice_v)
            
                # Shift X-axis view
                if now > WINDOW_SECONDS:
                    ax.set_xlim(now - WINDOW_SECONDS, now)
                
    except Exception:
        pass
    
    return line,

def get_points_chunk() -> list:
    nda_ecg = np.array(last_ecg_chunk, dtype=np.float64)
    nda_temp = np.array(last_temp_chunk, dtype=np.float64)
    nx, ny = lttbc.downsample(nda_temp, nda_ecg, int(len(last_ecg_chunk) * 0.6))
    return (ny - np.mean(ny)).tolist()
    # return np.clip((nda - np.mean(nda)) / np.std(nda), -2, 2).tolist()

def get_heart_rate() -> float:
    return now_ecg_data["avg_hr"]

# --- Run ---
def main() -> None:
    global fig, ax, line, socket_file, start_timestamp, last_ts

    # --- Setup Plot ---
    fig, ax = plt.subplots()
    line, = ax.plot([], [], lw=1.5, color='blue')
    ax.set_title("ECG Live Feed")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Voltage (V)")
    ax.grid(True)

    # --- Socket Connection ---
    print(f"Connecting to {ESP32_IP}...")
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(5)
    while True:
        try:
            client_socket.connect((ESP32_IP, PORT))
            break
        except ConnectionRefusedError:
            print("Connection refused, retrying in 1 second...")
            time.sleep(1)
    socket_file = client_socket.makefile('r')

    start_timestamp = time.time()
    last_ts = start_timestamp

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

        client_socket.close()

if __name__ == "__main__":
    main()