import platform
import uuid

SERVER_URL = "https://agentops-server-production.up.railway.app"
# SERVER_URL = "http://127.0.0.1:8001"
AUTH_TOKEN = "mysecrettoken"

AGENT_ID = f"{platform.node()}-{uuid.uuid4().hex[:6]}"
AGENT_OS = f"{platform.system()}"



# Reporting interval in seconds
REPORT_INTERVAL = 60

# Where to store offline payloads
OFFLINE_QUEUE_DIR = "offline_queue"