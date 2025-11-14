# 📚 AI-Agent for Google Scholar Alert Email  
Automated pipeline to fetch Google Scholar Alert emails, extract paper information, summarize content using Gemini, and generate clean, structured research reports.

This project helps researchers efficiently process Google Scholar Alerts without manually reading hundreds of emails. It downloads new alerts, parses them, summarizes papers using Gemini models, and outputs a consolidated report.

---

## ✨ Features

- 🔍 **Automatically fetch Google Scholar Alert** via IMAP  
- 📩 **Store email content locally** for later processing  
- 🧠 **Call Gemini CLI** to summarize papers (install Gemini CLI [here](https://github.com/google-gemini/gemini-cli)) 
- 📝 **Generate clean research reports** (Markdown or text)  
- 🎯 **Keyword filtering** for domain-specific relevance  
- ⚙️ **Fully configurable** via `config.py` and `.env` file

---

## 📦 Installation

### 1. Clone the repository
```
git clone https://github.com/LIMENGKE24/AI-Agent-GoogleScholarAlertEmail.git

cd AI-Agent-GoogleScholarAlertEmail
```

### 2. Create and activate a virtual environment (recommended)
```
conda create -n gmail_agent python=3.10 -y

conda activate gmail_agent
```
### 3. Install dependencies
```
pip install -r requirements.txt
```

---

## 🔐 Environment Variables (.env file required)
This project requires a `.env` file, which is NOT included in the repository for security reasons.
Please create your own `.env` file at the root of the project:
```
AI-Agent-GoogleScholarAlertEmail/.env
```
Add the following fields to it:
```
EMAIL_ADDRESS=your_email@address.com
EMAIL_PROVIDER=gmail
IMAP_PASSWORD=your Gmail app password (NOT LOGIN PASSWORD)
KEYWORDS=solid-state battery, ion-conductor (content you are interested in)
GEMINI_MODEL=gemini-2.5-pro
```
📌 Gmail IMAP requires app passwords to be enabled. See how to generate your own Gmail app password [here](https://support.google.com/mail/answer/185833?hl=en).

---

## ▶️ Usage
### Run the main script
```
python main.py
```
### Script will:
- Connect to Gmail IMAP  
- Fetch Google Scholar Alert emails  
- Parse the HTML content  
- Extract paper titles, authors, abstracts, and links  
- Send content to Gemini for summarization  
- Generate a structured report in output folder

---

## 📄 License
MIT License. Feel free to use, modify, and distribute.
