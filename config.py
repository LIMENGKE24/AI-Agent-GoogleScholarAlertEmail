import os
from dotenv import load_dotenv

# Email fetching settings
TODAY_ONLY = False # Set to True to fetch only today's emails
RECENT_COUNT = 20 # Number of recent emails to check

# Data directory
DATA_DIR = "Summarize_Output" # Directory to save outputs
os.makedirs(DATA_DIR, exist_ok=True)

# Sender to match
ALERT_SENDERS = {
    "scholaralerts-noreply@google.com"
}

# Keyword filtering settings
KEYWORDS = 'electrolyte, lithium, battery, solid-state, ion-conductor, solid electrolyte, diffusion, ion transport'
KEYWORDS = [k.strip().lower() for k in KEYWORDS.split(",") if k.strip()]

# AI model settings
CLI_CMD = 'claude' # Options: 'claude', 'gemini'
CLI_MODEL = 'claude-sonnet-4-5-20250929' # AI model name
MODEL_TEMPERATURE = 0.2

# Report generation settings
GENERATE_HTML = True # Generate HTML reports (recommended)
GENERATE_MARKDOWN = True # Keep markdown files as backup

# Email sending settings
ENABLE_EMAIL_SENDING = True # Set to False to disable email sending
REPORT_RECEIVER_EMAIL = "faker_zzz@outlook.com" # Email address to receive reports

# Load environment
load_dotenv()
EMAIL_ADDRESS = (os.getenv("EMAIL_ADDRESS") or "").strip()
IMAP_PASSWORD = (os.getenv("IMAP_PASSWORD") or "").strip()
SMTP_PASSWORD = IMAP_PASSWORD
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587