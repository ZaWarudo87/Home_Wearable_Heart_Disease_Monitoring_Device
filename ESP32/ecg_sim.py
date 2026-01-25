import socket
import time
import csv
import glob
import os
import random
import sys

# --- config ---
HOST = "0.0.0.0"
PORT = 80
DATA_FOLDER = "ECG_DATA"
SAMPLE_INTERVAL = 0.002  # 2 ms between samples (500 Hz)

def load_random_csv(folder: str) -> list:
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
            if "ecg_value" not in reader.fieldnames:
                print(f"Error: File {selected_file} is missing 'ecg_value' column")
                return None
            
            for row in reader:
                try:
                    val = (float(row["timestamp"]), float(row["ecg_value"]))
                    data_points.append(val)
                except ValueError:
                    continue
    except Exception as e:
        print(f"Failed to read file: {e}")
        return None
        
    print(f"Successfully read {len(data_points)} data points.")
    return data_points

def start_server() -> None:
    ecg_data = load_random_csv(DATA_FOLDER)
    if not ecg_data:
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
                data_index = 0
                total_samples = len(ecg_data)
                
                print("Starting data stream...")
                delta_time = time.time() - ecg_data[0][0]
                while True:
                    val = ecg_data[data_index][1]
                    data_index = (data_index + 1) % total_samples

                    elapsed = time.time() - delta_time
                    while elapsed < ecg_data[data_index][0]:
                        time.sleep(0.0005)
                        elapsed = time.time() - delta_time
                    
                    message = f"{val}\n"
                    client_socket.sendall(message.encode('utf-8'))
                        
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