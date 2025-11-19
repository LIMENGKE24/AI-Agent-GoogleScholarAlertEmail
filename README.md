# 📚 AI-Agent for Google Scholar Alert Email (AI4GS)

Automated pipeline to fetch Google Scholar Alert emails, extract paper information, summarize content using Claude/Gemini, and generate clean, structured research reports.

This project helps researchers efficiently process Google Scholar Alerts without manually reading hundreds of emails. It downloads new alerts, parses them, summarizes papers using Claude/Gemini CLI, and outputs a consolidated report.

---

## 🌟 Features

- 🔍 **Automatically fetch Google Scholar Alert emails** via IMAP
- 📩 **Store email content locally** for later processing
- 🧠 **Call Claude/Gemini CLI model** to summarize papers (install [Claude](https://github.com/anthropics/claude-code) or [Gemini](https://github.com/google-gemini/gemini-cli))
- 📝 **Generate clean research reports** in Markdown and HTML format
- 🎯 **Keyword filtering** for domain-specific relevance
- 📧 **Email reports automatically** to configured recipients
- ⚙️ **Fully configurable** via `config` file

---

## 📦 Installation

### 1. Clone the repository

```
git clone https://github.com/LIMENGKE24/AI-Agent-GoogleScholarAlertEmail.git
```
```
cd AI-Agent-GoogleScholarAlertEmail
```

### 2. Create and activate a virtual environment

```
conda create -n gmail_agent python=3.12 -y
```
```
conda activate gmail_agent
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

This project requires a `.env` file, which is NOT included in the repository for security reasons. Please create your own `.env` file at the root of the project:

```
AI-Agent-GoogleScholarAlertEmail/.env
```

Add the following fields to it:

```
EMAIL_ADDRESS=your_email@address.com
IMAP_PASSWORD=your Gmail app password (NOT LOGIN PASSWORD)
ANTHROPIC_API_KEY=your_API_key
```

📌 Gmail IMAP requires app passwords to be enabled. Learn how to generate your own app password [here](https://support.google.com/mail/answer/185833?hl=en).

---

## ▶️ Usage

### Run the main script

```
python main.py
```

### 🔧 Configuration

All configurable settings are located in `config.py`. You can adjust these parameters to change the behavior of the AI-agent.

- `TODAY_ONLY`: Set to True to fetch only the emails received today.
- `RECENT_COUNT`: Maximum number of recent emails to fetch.
- `ALERT_SENDERS`: Filter emails by sender. By default, only Google Scholar Alerts are processed.
- `KEYWORDS`: Only emails containing these keywords will be summarized.
- `CLI_CMD` and `CLI_MODEL`: Choose which AI model to use for summarization.
- `MODEL_TEMPERATURE`: Controls randomness in output.
- `ENABLE_EMAIL_SENDING`: Set to False to disable automatic email sending.
- `REPORT_RECEIVER_EMAIL`: Email address where summary reports will be sent.

---

## 📄 License

MIT License. Free to use, modify, and distribute.
