import os
from dotenv import load_dotenv

load_dotenv()

LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://127.0.0.1:1234")
PLANNER_MODEL = os.getenv("PLANNER_MODEL", "qwen/qwen3-vl-4b")
CRITIC_MODEL = os.getenv("CRITIC_MODEL", "mistralai/mistral-7b-instruct-v0.3")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# adding security realted configuration keys :

# Security and Rate Limiting Configurations:
API_KEY = os.getenv("API_KEY", "dev-key-change-in-production")  # API key for authenticating requests
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "1000"))  # Max length of incoming messages
MAX_USER_ID_LENGTH = int(os.getenv("MAX_USER_ID_LENGTH", "50"))  # Max length of user IDs
MAX_CORRECTION_LENGTH = int(os.getenv("MAX_CORRECTION_LENGTH", "500"))  # Max length of user corrections

# Rate limiting: /chat endpoint
CHAT_RATE_LIMIT_REQUESTS = int(os.getenv("CHAT_RATE_LIMIT_REQUESTS", "10"))
CHAT_RATE_LIMIT_WINDOW_SEC = int(os.getenv("CHAT_RATE_LIMIT_WINDOW_SEC", "60"))

# Rate Limiting: /debug endpoints
DEBUG_RATE_LIMIT_REQUESTS = int(os.getenv("DEBUG_RATE_LIMIT_REQUESTS", "50"))
DEBUG_RATE_LIMIT_WINDOW_SEC = int(os.getenv("DEBUG_RATE_LIMIT_WINDOW_SEC", "60"))

# Ratre limiting: /feedback endpoint
FEEDBACK_RATE_LIMIT_REQUESTS = int(os.getenv("FEEDBACK_RATE_LIMIT_REQUESTS", "20"))
FEEDBACK_RATE_LIMIT_WINDOW_SEC = int(os.getenv("FEEDBACK_RATE_LIMIT_WINDOW_SEC", "60"))