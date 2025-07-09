# agent.py

import psutil
import time
import json
import requests
import platform
from datetime import datetime

SERVER_URL = "http://yourserver.com:5000/system-data"  # ⬅️ your API endpoint
INTERVAL = 10  # seconds

def collect_system_data():
    data = {
        "timestamp": datetime.utcnow().isoformat(),
        "hostname": platform.node(),
        "os": platform.platform(),
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent,
        "battery": None,
        "uptime": time.time() - psutil.boot_time(),
        "processes": []
    }

    battery = psutil.sensors_battery()
    if battery:
        data["battery"] = {
            "percent": battery.percent,
            "plugged_in": battery.power_plugged,
            "secs_left": battery.secsleft
        }

    # Optional: collect top N processes
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        data["processes"].append(proc.info)

    return data

# def send_data(payload):
#     try:
#         response = requests.post(SERVER_URL, json=payload, timeout=5)
#         response.raise_for_status()
#         print(f"[{datetime.now()}] ✅ Data sent successfully")
#     except requests.RequestException as e:
#         print(f"[{datetime.now()}] ❌ Failed to send data:", e)

# def main():
#     while True:
#         payload = collect_system_data()
#         send_data(payload)
        # time.sleep(INTERVAL)

