import csv
import glob
import os
import random
import socket
import time

# --- config ---
HOST = "0.0.0.0"
PORT = 80
DATA_FOLDER = "ECG_DATA"
REST_FOLDER = os.path.join(DATA_FOLDER, "rest")
EXERCISE_FOLDER = os.path.join(DATA_FOLDER, "exercise")
SAMPLE_INTERVAL = 0.00625  # 160 Hz

def load_random_csv(folder: str, is_rest: bool = True) -> list:
    if not os.path.exists(folder):
        print(f"Error: '{folder}' not found.")
        return None

    csv_files = glob.glob(os.path.join(folder, '*.csv'))
    if not csv_files:
        print(f"Error: No .csv files found in '{folder}'.")
        return None

    selected_file = random.choice(csv_files)
    print(f"--- Reading file: {selected_file} ---")

    data_points = []
    try:
        with open(selected_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)            
            for row in reader:
                try:
                    if is_rest:
                        val = (float(row["timestamp"]), float(row["ecg_value"]))
                    else:
                        val = (float(row["IsExercise"]), float(row["Voltage"]))
                    data_points.append(val)
                except ValueError:
                    continue
    except Exception as e:
        print(f"Failed to read file: {e}")
        return None
        
    print(f"Successfully read {len(data_points)} data points.")
    return data_points

def stream_data(client_socket, ecg_data: list, is_exercise: bool, t_us: int) -> int:
    for idk, val in ecg_data:
        if is_exercise:
            exercise = int(idk)
        else:
            exercise = 0
        message = f"{t_us},{exercise},{val:.2f}\n"
        client_socket.sendall(message.encode('utf-8'))
        t_us += int(SAMPLE_INTERVAL * 1000000)
        if t_us >= 4294967296:  # unsigned long overflow like ESP32 micros()
            t_us -= 4294967296
        time.sleep(SAMPLE_INTERVAL)
    return t_us

def start_server() -> None:
    for folder in (REST_FOLDER, EXERCISE_FOLDER):
        if not os.path.exists(folder):
            print(f"Error: '{folder}' not found.")
            return
        if not glob.glob(os.path.join(folder, '*.csv')):
            print(f"Error: No .csv files found in '{folder}'.")
            return

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        server_socket.settimeout(1.0)
        print(f"\n--- Python ECG Simulator Started ---")
        print(f"IP: {socket.gethostbyname(socket.gethostname())}")
        print(f"Port: {PORT}")
        print("Waiting for client connection...")

        while True:
            try:
                client_socket, client_address = server_socket.accept()
                print(f"\nConnection successful! From: {client_address}")
            except socket.timeout:
                continue
            
            try:
                t_us = 0
                print("Starting data stream...")
                
                while True:
                    # --- REST ---
                    rest_data = load_random_csv(REST_FOLDER, True)
                    if not rest_data:
                        break
                    print("[REST] Streaming...")
                    t_us = stream_data(client_socket, rest_data, False, t_us)

                    # --- EXERCISE ---
                    exercise_data = load_random_csv(EXERCISE_FOLDER, False)
                    if not exercise_data:
                        break
                    print("[EXERCISE] Streaming...")
                    t_us = stream_data(client_socket, exercise_data, True, t_us)
                        
            except (ConnectionResetError, BrokenPipeError):
                print("Client disconnected. Waiting for new connection...")
            except KeyboardInterrupt:
                print("\nServer stopping...")
                break
            finally:
                client_socket.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()