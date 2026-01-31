import socket
import csv
import os
from datetime import datetime

ESP32_IP = '127.0.0.1'
PORT = 80
BASE_DIR = "ecg_records"

def start_receiver():
    os.makedirs(BASE_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    FILE_NAME = os.path.join(BASE_DIR, f"ecg_data_{timestamp}.csv")
    # ===================================

    print(f"Connecting to {ESP32_IP}...")
    print(f"Saving data to: {FILE_NAME}")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ESP32_IP, PORT))
            print("Connected! Recording data... (Press Ctrl+C to stop)")

            with open(FILE_NAME, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["IsExercise", "Voltage"])

                buffer = ""  # holds incomplete line fragments

                while True:
                    chunk = s.recv(1024)
                    if not chunk:
                        break

                    buffer += chunk.decode("utf-8", errors="replace")

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue

                        # print(f"Received line: {line}")

                        if "," not in line:
                            continue

                        mode, voltage = line.split(",", 1)
                        mode = mode.strip()
                        voltage = voltage.strip().strip('"')

                        writer.writerow([mode, voltage])

    except KeyboardInterrupt:
        print("\nStopped. Data saved.")
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    start_receiver()
