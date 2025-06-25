import time
import requests
import logging
from logging.handlers import RotatingFileHandler

from app.config import SERVER_URL, AGENT_ID, AUTH_TOKEN,AGENT_OS
from app.command_executor import run_command
from app.system_info import (
    get_basic_info,
    get_installed_packages,
    get_running_services,
    get_log_contents,get_live_background_services
)
from app.security_scanner import scan_viruses_and_vulnerabilities

# Logging setup with rotation
log_handler = RotatingFileHandler("agent.log", maxBytes=1_000_000, backupCount=3)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[log_handler, logging.StreamHandler()]
)

HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}


def start_agent():
    logging.info(f"🛡️ Agent ID: {AGENT_ID}")
    logging.info("📡 Registering agent...")
    logging.info(f"Agent OS {AGENT_OS}")

    try:
        print(AGENT_OS)
        res = requests.post(
            f"{SERVER_URL}/agents/register",
            json={"agent_id": AGENT_ID,"os":AGENT_OS},
            headers=HEADERS
        )
        res.raise_for_status()
        logging.info(f"✅ Registered successfully: {res.json()}")
    except Exception as e:
        logging.error(f"❌ Registration failed: {e}")
        return

    # Command polling loop
    while True:
        try:
            res = requests.get(
                f"{SERVER_URL}/commands/get/{AGENT_ID}",
                headers=HEADERS
            )
            res.raise_for_status()
            data = res.json()
            command = data.get("command")

            if command:
                logging.info(f"🟢 Command received: {command}")

                # Handle predefined commands
                if command == "get_info":
                    output = str(get_basic_info())
                elif command == "get_logs":
                    output = get_log_contents()
                elif command == "get_packages":
                    output = get_installed_packages()
                elif command == "get_services":
                    output = get_running_services()
                elif command == "get_live_services":
                    output = str(get_live_background_services())
                elif command == "scan_security":
                    output = scan_viruses_and_vulnerabilities()
                else:
                    output = run_command(command)

                # Send result
                result = {
                    "agent_id": AGENT_ID,
                    "output": output,
                    "command":command
                }

                try:
                    post_res = requests.post(
                        f"{SERVER_URL}/agents/result",
                        json=result,
                        headers=HEADERS
                    )
                    post_res.raise_for_status()
                    logging.info("📤 Command result sent to server")
                except Exception as e:
                    logging.error(f"❌ Failed to send result: {e}")

            time.sleep(5)

        except Exception as e:
            logging.error(f"⚠️ Error during polling: {e}")
            time.sleep(10)
