# app/main.py

import os
import sys
import platform
import logging
from app.client import AgentClient

def get_log_path():
    system = platform.system().lower()

    if system == "windows":
        # e.g. C:\Users\John\AppData\Local\AgentOps\agent.log
        base_dir = os.environ.get("LOCALAPPDATA", os.getcwd())
        log_dir = os.path.join(base_dir, "AgentOps")

    elif system == "darwin":
        # e.g. /Users/john/Library/Logs/AgentOps/agent.log
        base_dir = os.path.expanduser("~/Library/Logs")
        log_dir = os.path.join(base_dir, "AgentOps")

    elif system == "linux":
        # e.g. /home/john/.local/share/AgentOps/logs/agent.log
        base_dir = os.path.expanduser("~/.local/share")
        log_dir = os.path.join(base_dir, "AgentOps", "logs")

    else:
        # fallback for unknown OS
        log_dir = os.path.join(os.getcwd(), "logs")

    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "agent.log")


log_file = get_log_path()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

if __name__ == "__main__":
    logging.info("Starting Agent Client...")
    client = AgentClient()
    client.start()
