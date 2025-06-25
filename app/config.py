import platform
import uuid

SERVER_URL = "https://agentops-server-production.up.railway.app/"
AUTH_TOKEN = "mysecrettoken"

AGENT_ID = f"{platform.node()}-{uuid.uuid4().hex[:6]}"
AGENT_OS = f"{platform.system()}"
