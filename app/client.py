# agentops/client.py

import os
import time
import platform
import requests
import logging
import json
import sys

from app.config import (
    SERVER_URL,
    AGENT_ID,
    AUTH_TOKEN,
    AGENT_OS,
    REPORT_INTERVAL,
)
from app.system_info import (
    get_basic_info,
    get_installed_packages,
    get_running_services,
    get_log_contents,
    get_live_background_services,
)
from app.command_executor import run_command
from app.log_collector import (
    LinuxLogCollector,
    MacOSLogCollector,
    WindowsLogCollector,
)
from app.error_detector import ErrorDetector
from app.security_scanner import SecurityScanner

from app.db_queue import DBQueue
from concurrent.futures import ThreadPoolExecutor

HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}

MAX_PAYLOAD_SIZE = 5 * 1024 * 1024  # 5MB
MAX_LOG_LINES = 1000


class AgentClient:
    def __init__(self):
        self.agent_id = AGENT_ID
        self.agent_os = AGENT_OS or platform.system().lower()
        self.collector = self._get_log_collector()
        self.error_detector = ErrorDetector()
        self.security_scanner = SecurityScanner()
        self.local_queue = DBQueue()
        self.previous_logs = ""
        self.executor = ThreadPoolExecutor(max_workers=5)

    def _get_log_collector(self):
        os_name = self.agent_os.lower()
        print(os_name)
        print(f"Detected OS: {os_name}")
        if "linux" in os_name:
            return LinuxLogCollector()
        elif "darwin" in os_name:
            return MacOSLogCollector()
        elif "windows" in os_name:
            return WindowsLogCollector()
        else:
            raise Exception(f"Unsupported OS: {self.agent_os}")

    def register(self):
        print(f"Registering agent_id: {self.agent_id}")
        try:
            res = requests.post(
                f"{SERVER_URL}/agents/register",
                json={
                    "agent_id": self.agent_id,
                    "os": self.agent_os,
                },
                headers=HEADERS,
                timeout=10,
            )
            res.raise_for_status()
            logging.info(f"✅ Registered successfully: {res.json()}")
            return True
        except Exception as e:
            logging.error(f"❌ Registration failed: {e}")
            return False

    def start(self):
        if not self.register():
            return

        last_report_time = 0

        while True:
            current_time = time.time()

            if current_time - last_report_time >= REPORT_INTERVAL:
                self.executor.submit(self._collect_and_send)
                self.executor.submit(self.local_queue.flush, self._post_from_queue)
                last_report_time = current_time

            self.executor.submit(self._check_for_commands)
            time.sleep(5)

    def _check_for_commands(self):
        try:
            res = requests.get(
                f"{SERVER_URL}/commands/get/{self.agent_id}",
                headers=HEADERS,
                timeout=10,
            )
            res.raise_for_status()
            data = res.json()
            command = data.get("command")
            if command:
                logging.info(f"🟢 Command received: {command}")
                self.executor.submit(self._execute_command, command)
            else:
                logging.info(f"🟢 No command received. Running get_all by default.")
                self.executor.submit(self._execute_command, "get_all")
        except Exception as e:
            logging.error(f"⚠️ Error checking for commands: {e}")

    def _execute_command(self, command):
        logging.info(f"Executing command: {command}")

        if command == "get_info":
            output = get_basic_info()
            self._post_result(command, output)

        elif command == "get_logs":
            logs = self.collector.collect_logs()
            output = logs if logs else "No logs collected."
            self._post_result(command, output)

        elif command == "get_packages":
            output = get_installed_packages()
            self._post_result(command, output)

        elif command == "get_services":
            output = get_running_services()
            self._post_result(command, output)

        elif command == "get_live_services":
            output = get_live_background_services()
            self._post_result(command, output)

        elif command == "scan_security":
            output = self.security_scanner.scan()
            self._post_result(command, output)

        elif command == "get_all":
            logging.info("🟢 Running get_all…")
            print("logs-list")
            logs = self._get_log_collector()
            print(json.dumps(logs.__dict__))
            print("logs-list")
            all_data = {
                "system_info": get_basic_info(),
                "logs": logs if logs else "No logs collected.",
                "packages": get_installed_packages(),
                "services": get_running_services(),
                "live_services": get_live_background_services(),
                # "security_findings": self.security_scanner.scan(),
            }
            self._post_result(command, all_data)

        else:
            output = run_command(command)
            self._post_result(command, output)

    def _post_result(self, command, output):
        result_payload = {
            "agent_id": self.agent_id,
            "command": command,
            "output": output,
        }
        self._try_post("/agents/result", result_payload)

    def _collect_and_send(self):
        logging.info("🔄 Running automatic data collection...")

        self.executor.submit(self._send_payload, "/agents/system_info", {
            "agent_id": self.agent_id,
            "system_info": get_basic_info(),
        })

        logs = self.collector.collect_logs()
        new_logs = self._diff_logs(logs)
        if new_logs:
            self.executor.submit(self._send_payload, "/agents/logs", {
                "agent_id": self.agent_id,
                "logs": new_logs,
            })

            errors = self.error_detector.extract_errors(
                new_logs, source=self.agent_os
            )
            if errors:
                self.executor.submit(self._send_payload, "/agents/errors", {
                    "agent_id": self.agent_id,
                    "errors": errors,
                })

        self.executor.submit(self._send_payload, "/agents/security", {
            "agent_id": self.agent_id,
            "findings": self.security_scanner.scan(),
        })

        self.executor.submit(self._send_payload, "/agents/packages", {
            "agent_id": self.agent_id,
            "packages": get_installed_packages(),
        })

        self.executor.submit(self._send_payload, "/agents/services", {
            "agent_id": self.agent_id,
            "services": get_running_services(),
            "live_services": get_live_background_services(),
        })

        logging.info("✅ Data collection cycle complete.")

    def _diff_logs(self, logs):
        if not logs:
            return ""

        prev_lines = set(self.previous_logs.splitlines())
        new_lines = [
            line for line in logs.splitlines()
            if line not in prev_lines
        ]

        all_lines = logs.splitlines()
        self.previous_logs = "\n".join(all_lines[-MAX_LOG_LINES:])
        return "\n".join(new_lines)

    def _try_post(self, path, payload):
        try:
            payload_size = sys.getsizeof(json.dumps(payload))
            if payload_size > MAX_PAYLOAD_SIZE:
                logging.warning(
                    f"⚠️ Skipping large payload to {path} ({payload_size} bytes)"
                )
                return
            self._post(path, payload)
        except Exception:
            self.local_queue.enqueue({
                "path": path,
                "payload": payload,
            })

    def _send_payload(self, path, payload):
        try:
            self._try_post(path, payload)
        except Exception as e:
            logging.error(f"❌ Failed to send payload to {path}: {e}")

    def _post(self, path, payload):
        res = requests.post(
            f"{SERVER_URL}{path}",
            json=payload,
            headers=HEADERS,
            timeout=10,
        )
        res.raise_for_status()
        logging.info(f"📤 Data sent to {path}.")

    def _post_from_queue(self, queued_payload):
        self._post(queued_payload["path"], queued_payload["payload"])
