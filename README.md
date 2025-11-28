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
- ⚙️ **Easy Configuration** via interactive CLI or `.env` file

---

## 📦 Installation

Simply install the package from PyPI:

```bash
pip install ai4gs
```

---

## ▶️ Usage

### 1. Initialize Configuration

First, run the initialization command to set up your credentials and preferences. This will create a `.env` file in your current directory.

```bash
ai4gs init
```

Follow the interactive prompts to enter your:
- Gmail Address
- Gmail App Password (Not login password, and required for IMAP access. [Generate one here](https://support.google.com/mail/answer/185833?hl=en))
- Anthropic API Key (Required for AI summarization)
- Research Keywords (Comma-separated list of topics, e.g., "machine learning, climate change")

### 2. Run the Agent

Start the research automation pipeline:

```bash
ai4gs run
```

### 🔧 Configuration

The `ai4gs init` command creates a `.env` file where you can adjust settings. You can also manually edit this file.

**Key Settings:**
- `KEYWORDS`: Comma-separated list of research topics.
- `REPORT_RECEIVER_EMAIL`: Where to send the report.
- `RECENT_COUNT`: Number of recent emails to check (default: 10).
- `TODAY_ONLY`: Set to `True` to only check today's emails.

---

## 📄 License

MIT License. Free to use, modify, and distribute.
