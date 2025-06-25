import platform
import uuid

SERVER_URL = "http://127.0.0.1:8000"
AUTH_TOKEN = "mysecrettoken"

AGENT_ID = f"{platform.node()}-{uuid.uuid4().hex[:6]}"
AGENT_OS = f"{platform.system()}"
