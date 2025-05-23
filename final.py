import psutil
import time
import pandas as pd
import joblib
import threading
from sklearn.linear_model import LinearRegression
import tkinter as tk
from tkinter import Label
import matplotlib.pyplot as plt
import numpy as np
from sklearn.preprocessing import StandardScaler

# ---------- Module 1: Data Collection ----------
def collect_system_metrics(log_file='system_data.csv', duration=60, interval=1):
    columns = ['timestamp', 'cpu_usage', 'memory_usage', 'disk_usage', 'network_sent', 'network_recv']
    df = pd.DataFrame(columns=columns)

    for _ in range(duration):
        timestamp = time.time()
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        net = psutil.net_io_counters()
        net_sent = net.bytes_sent / (1024 * 1024)
        net_recv = net.bytes_recv / (1024 * 1024)

        df = df.append({
            'timestamp': timestamp,
            'cpu_usage': cpu,
            'memory_usage': mem,
            'disk_usage': disk,
            'network_sent': net_sent,
            'network_recv': net_recv
        }, ignore_index=True)

        print(f"Logged: CPU {cpu}%, MEM {mem}%, DISK {disk}%")
        time.sleep(interval)

    df.to_csv(log_file, index=False)

# ---------- Module 2: Model Training ----------
def train_prediction_model(data_file='system_data.csv', model_file='resource_predictor.pkl'):
    df = pd.read_csv(data_file).dropna()
    
    if df.empty:
        print("Error: Collected data is empty. Ensure data is being logged correctly.")
        return

    X = df[['cpu_usage', 'memory_usage', 'disk_usage', 'network_sent', 'network_recv']]
    y_cpu = df['cpu_usage'].shift(-1).fillna(method='ffill')
    y_mem = df['memory_usage'].shift(-1).fillna(method='ffill')

    # Initialize StandardScaler for feature scaling
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train models for CPU and Memory usage
    model_cpu = LinearRegression().fit(X_scaled, y_cpu)
    model_mem = LinearRegression().fit(X_scaled, y_mem)

    # Save models and scaler
    joblib.dump((model_cpu, model_mem, scaler), model_file)
    print("✅ Models for CPU and Memory trained and saved.")

# ---------- Module 3: GUI with Predictions ----------
def start_gui(model_file='resource_predictor.pkl'):
    model_cpu, model_mem, scaler = joblib.load(model_file)

    def update_gui():
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        net = psutil.net_io_counters()
        net_sent = net.bytes_sent / (1024 * 1024)
        net_recv = net.bytes_recv / (1024 * 1024)

        input_data = pd.DataFrame([[cpu, mem, disk, net_sent, net_recv]],
                                  columns=['cpu_usage', 'memory_usage', 'disk_usage', 'network_sent', 'network_recv'])

        # Scale the input data using the same scaler used in training
        input_scaled = scaler.transform(input_data)

        # Predict CPU and Memory usage
        pred_cpu = model_cpu.predict(input_scaled)[0]
        pred_mem = model_mem.predict(input_scaled)[0]

        # Clip the predictions to ensure they are within the 0-100% range
        pred_cpu = np.clip(pred_cpu, 0, 100)
        pred_mem = np.clip(pred_mem, 0, 100)

        # Update GUI labels with current and predicted values
        label_current_cpu.config(text=f"Current CPU Usage: {cpu:.2f}%")
        label_current_mem.config(text=f"Current Memory Usage: {mem:.2f}%")
        label_pred_cpu.config(text=f"Predicted CPU Usage: {pred_cpu:.2f}%")
        label_pred_mem.config(text=f"Predicted Memory Usage: {pred_mem:.2f}%")

        if pred_cpu > 80 or pred_mem > 80:
            warning_label.config(text="⚠️ High resource usage predicted!", fg='red')
        else:
            warning_label.config(text="System stable.", fg='green')

        root.after(5000, update_gui)

    # GUI Setup
    root = tk.Tk()
    root.title("System Resource Monitor")
    root.geometry("400x250")

    label_current_cpu = Label(root, text="Current CPU Usage: ", font=('Arial', 12))
    label_current_cpu.pack(pady=5)

    label_current_mem = Label(root, text="Current Memory Usage: ", font=('Arial', 12))
    label_current_mem.pack(pady=5)

    label_pred_cpu = Label(root, text="Predicted CPU Usage: ", font=('Arial', 12))
    label_pred_cpu.pack(pady=5)

    label_pred_mem = Label(root, text="Predicted Memory Usage: ", font=('Arial', 12))
    label_pred_mem.pack(pady=5)

    warning_label = Label(root, text="", font=('Arial', 12, 'bold'))
    warning_label.pack(pady=10)

    update_gui()
    root.mainloop()

# ---------- Optional: Plotting ----------
def plot_resource_usage(data_file='system_data.csv'):
    df = pd.read_csv(data_file)
    plt.figure(figsize=(10, 5))
    plt.plot(df['timestamp'], df['cpu_usage'], label='CPU Usage')
    plt.plot(df['timestamp'], df['memory_usage'], label='Memory Usage')
    plt.xlabel('Timestamp')
    plt.ylabel('Usage (%)')
    plt.title('System Resource Usage')
    plt.legend()
    plt.show()

# ---------- Main Pipeline ----------
def main():
    print("Starting system monitoring...")
    collect_thread = threading.Thread(target=collect_system_metrics, args=('system_data.csv', 30, 2))
    collect_thread.start()
    collect_thread.join()

    print("Training prediction models...")
    train_prediction_model('system_data.csv', 'resource_predictor.pkl')

    print("Launching GUI...")
    start_gui('resource_predictor.pkl')

if __name__ == "__main__":
    main()
