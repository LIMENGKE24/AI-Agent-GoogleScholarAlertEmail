import os
from dotenv import load_dotenv

# Email fetching settings
TODAY_ONLY = True
RECENT_COUNT = 100

# Data directory
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Sender(s) to match
ALERT_SENDERS = {
    "scholaralerts-noreply@google.com"
}

# Load environment
load_dotenv()
EMAIL_ADDRESS = (os.getenv("EMAIL_ADDRESS") or "").strip()
IMAP_PASSWORD = (os.getenv("IMAP_PASSWORD") or "").strip()
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

# Summarization (Gemini CLI)
GEMINI_CMD = (os.getenv("GEMINI_CMD") or "gemini").strip()
GEMINI_MODEL = (os.getenv("GEMINI_MODEL") or "gemini-1.5-flash").strip()
GEMINI_EXTRA_ARGS = (os.getenv("GEMINI_EXTRA_ARGS") or "").strip()
KEYWORDS = [k.strip().lower() for k in (os.getenv("KEYWORDS") or "").split(",") if k.strip()]