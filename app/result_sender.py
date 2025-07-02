# agentops/result_sender.py

import requests
from agentops.config import SERVER_URL, AGENT_ID, AUTH_TOKEN

class ResultSender:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}"
        }

    def send_logs(self, logs):
        payload = {
            "agent_id": AGENT_ID,
            "logs": logs
        }
        return self._post("/agents/logs", payload)

    def send_errors(self, errors):
        payload = {
            "agent_id": AGENT_ID,
            "errors": errors
        }
        return self._post("/agents/errors", payload)

    def send_security(self, findings):
        payload = {
            "agent_id": AGENT_ID,
            "findings": findings
        }
        return self._post("/agents/security", payload)

    def send_system_info(self, info):
        payload = {
            "agent_id": AGENT_ID,
            "system_info": info
        }
        return self._post("/agents/system_info", payload)

    def _post(self, path, payload):
        try:
            res = requests.post(
                f"{SERVER_URL}{path}",
                json=payload,
                headers=self.headers
            )
            res.raise_for_status()
            return True
        except Exception as e:
            print(f"Upload error {path}: {e}")
            return False
