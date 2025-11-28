import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Load from current directory (Highest priority)
load_dotenv()

# 2. Load from user home directory (Global config)
home_env = Path.home() / ".ai4gs.env"
if home_env.exists():
    load_dotenv(dotenv_path=home_env)

def get_env_bool(key, default=False):
    val = os.getenv(key, str(default)).lower()
    return val in ("true", "1", "yes", "on")

def get_env_list(key, default=""):
    val = os.getenv(key, default)
    return [k.strip().lower() for k in val.split(",") if k.strip()]

# Email fetching settings
TODAY_ONLY = get_env_bool("TODAY_ONLY", False) # Set to True to fetch only today's emails
RECENT_COUNT = int(os.getenv("RECENT_COUNT", "10")) # Number of recent emails to check

# Data directory
DATA_DIR = os.getenv("DATA_DIR", "Summarize_Output") # Directory to save outputs
os.makedirs(DATA_DIR, exist_ok=True)

# Sender to match
ALERT_SENDERS = {
    "scholaralerts-noreply@google.com"
}

# Keyword filtering settings
# Default keywords if not provided in env
DEFAULT_KEYWORDS = 'electrolyte, lithium, battery, solid-state, ion-conductor, solid electrolyte, diffusion, ion transport'
KEYWORDS = get_env_list("KEYWORDS", DEFAULT_KEYWORDS)

# AI model settings
CLI_CMD = os.getenv("CLI_CMD", 'claude') # Options: 'claude', 'gemini'
CLI_MODEL = os.getenv("CLI_MODEL", 'claude-sonnet-4-5-20250929') # AI model name
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.2"))

# Report generation settings
GENERATE_HTML = get_env_bool("GENERATE_HTML", True) # Generate HTML reports (recommended)
GENERATE_MARKDOWN = get_env_bool("GENERATE_MARKDOWN", True) # Keep markdown files as backup

# Email sending settings
ENABLE_EMAIL_SENDING = get_env_bool("ENABLE_EMAIL_SENDING", True) # Set to False to disable email sending
REPORT_RECEIVER_EMAIL = os.getenv("REPORT_RECEIVER_EMAIL", "faker_zzz@outlook.com") # Email address to receive reports

# Credentials
EMAIL_ADDRESS = (os.getenv("EMAIL_ADDRESS") or "").strip()
IMAP_PASSWORD = (os.getenv("IMAP_PASSWORD") or "").strip()
SMTP_PASSWORD = IMAP_PASSWORD
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
