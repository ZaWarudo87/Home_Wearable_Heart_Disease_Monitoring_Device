import os
import socket
import csv
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# --- Configuration ---
ESP32_IP = '127.0.0.1' 
PORT = 80
WINDOW_SECONDS = 10  # How many seconds to show on the live graph
SAVE_DATA = True

# Data storage
all_times = []
all_values = []

def init():
    ax.set_xlim(0, WINDOW_SECONDS)
    ax.set_ylim(-2, 5) 
    return line,

def update(frame):
    try:
        line_data = socket_file.readline().strip()
        if line_data:
            val = float(line_data)
            now_timestamp = time.time()
            now = now_timestamp - start_timestamp
            
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

# --- TODO: give me these data ---
# def get_points_chunk(index: int = 0, chunk_size: int = 20) -> list:
#     return []

# def get_heart_rate(ecg_points: list) -> int:
#     return 0

# --- Run ---
def main() -> None:
    global fig, ax, line, socket_file, start_timestamp

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
    client_socket.connect((ESP32_IP, PORT))
    socket_file = client_socket.makefile('r')

    start_timestamp = time.time()

    try:
        print("Recording... Close plot window or press Ctrl+C to save and exit.")
        ani = FuncAnimation(fig, update, init_func=init, blit=True, interval=1, cache_frame_data=False)
        plt.show()
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