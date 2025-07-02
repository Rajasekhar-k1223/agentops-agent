# app/main.py

import logging
from app.client import AgentClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("agent.log"),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    logging.info("Starting Agent Client...")
    client = AgentClient()
    client.start()
