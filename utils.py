import os
import imaplib
import smtplib
import email
from email.utils import parsedate_to_datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from bs4 import BeautifulSoup
from datetime import datetime
import json
import subprocess
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Import config values
from config import (
    EMAIL_ADDRESS, IMAP_PASSWORD, SMTP_PASSWORD,
    IMAP_SERVER, IMAP_PORT, SMTP_SERVER, SMTP_PORT,
    ALERT_SENDERS, REPORT_RECEIVER_EMAIL, ENABLE_EMAIL_SENDING,
    CLI_CMD, CLI_MODEL, MODEL_TEMPERATURE,
    KEYWORDS,
    TODAY_ONLY, RECENT_COUNT,
    DATA_DIR
)


def assert_env():
    if not EMAIL_ADDRESS or not IMAP_PASSWORD:
        raise RuntimeError("Missing EMAIL_ADDRESS or IMAP_PASSWORD in .env")


def connect_imap_gmail():
    assert_env()
    M = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    M.login(EMAIL_ADDRESS, IMAP_PASSWORD)
    return M


def list_mailboxes(M):
    typ, data = M.list()
    if typ != "OK":
        raise RuntimeError("LIST failed.")
    names = []
    for line in data:
        s = line.decode("utf-8", errors="ignore")
        if ' "/" ' in s:
            name = s.split(' "/" ')[-1].strip().strip('"')
        else:
            name = s.split()[-1].strip('"')
        names.append((s, name))
    return names


def find_all_mail_mailbox(M):
    names = list_mailboxes(M)
    for raw, name in names:
        if "\\All" in raw:
            return name
    for raw, name in names:
        if "All Mail" in name:
            return name
    return None


def safe_select(M, mailbox):
    typ, dat = M.select(f'"{mailbox}"')
    if typ == "OK":
        return mailbox
    typ, dat = M.select(mailbox)
    if typ == "OK":
        return mailbox
    typ, dat = M.select("INBOX")
    if typ != "OK":
        raise RuntimeError(f"SELECT failed for {mailbox} and INBOX: {typ} {dat}")
    return "INBOX"


def get_recent_uids(M, max_count=100):
    typ, data = M.uid("SEARCH", None, "ALL")
    if typ != "OK":
        raise RuntimeError(f"UID SEARCH ALL failed: {typ} {data}")
    uids = data[0].split() if data and data[0] else []
    return uids[-max_count:] if uids else []


def fetch_header(M, uid):
    typ, data = M.uid("FETCH", uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
    if typ != "OK" or not data:
        return None
    raw = data[0][1]
    msg = email.message_from_bytes(raw)
    return {
        "from": msg.get("From", ""),
        "subject": msg.get("Subject", ""),
        "date": msg.get("Date", ""),
        "dt": safe_parse_date(msg.get("Date", "")),
    }


def safe_parse_date(date_hdr):
    try:
        return parsedate_to_datetime(date_hdr)
    except Exception:
        return None


def normalize_from(from_hdr):
    try:
        return email.utils.parseaddr(from_hdr)[1].lower()
    except Exception:
        return (from_hdr or "").lower().strip()


def is_today(dt):
    if not dt:
        return False
    local_dt = dt.astimezone() if dt.tzinfo else dt
    return local_dt.date() == datetime.now().date()


def fetch_body_html(M, uid):
    typ, data = M.uid("FETCH", uid, "(RFC822)")
    if typ != "OK" or not data:
        return ""
    raw_msg = data[0][1]
    msg = email.message_from_bytes(raw_msg)
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                charset = part.get_content_charset() or "utf-8"
                payload = part.get_payload(decode=True)
                if payload is not None:
                    return payload.decode(charset, errors="ignore")
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                charset = part.get_content_charset() or "utf-8"
                payload = part.get_payload(decode=True)
                if payload is not None:
                    text = payload.decode(charset, errors="ignore")
                    return f"<html><body><pre>{text}</pre></body></html>"
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            content = payload.decode(charset, errors="ignore")
            if msg.get_content_type() == "text/html":
                return content
            if msg.get_content_type() == "text/plain":
                return f"<html><body><pre>{content}</pre></body></html>"
    return ""


def extract_items_from_html(html):
    soup = BeautifulSoup(html, "lxml")
    items = []
    anchors = []
    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        href = a["href"]
        if not title or len(title) < 4:
            continue
        if ("scholar.google" in href) or href.startswith("http"):
            anchors.append(a)

    seen = set()
    for a in anchors:
        title = a.get_text(strip=True)
        link = a["href"]
        abstract = None
        parent = a.find_parent(["div", "td", "tr", "p", "li"])
        if parent:
            text = parent.get_text(" ", strip=True)
            text_clean = text.replace(title, "").strip()
            abstract = text_clean or None
        if not abstract:
            sib = a.find_next_sibling()
            if sib:
                abstract = sib.get_text(" ", strip=True)
        key = (title, link)
        if key in seen:
            continue
        seen.add(key)
        items.append({"title": title, "link": link, "abstract": abstract})
    return items


def keyword_filter(items, keywords):
    if not keywords:
        return items
    selected = []
    for it in items:
        blob = " ".join([
            it.get("title", ""),
            it.get("abstract", "") or "",
        ]).lower()
        if any(k in blob for k in keywords):
            selected.append(it)
    return selected


def save_items(items, tag):
    path_jsonl = os.path.join(DATA_DIR, f"scholar_items_{tag}.jsonl")
    path_md = os.path.join(DATA_DIR, f"scholar_items_{tag}.md")
    with open(path_jsonl, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    with open(path_md, "w", encoding="utf-8") as f:
        f.write("# Google Scholar Alerts (Filtered)\n\n")
        for i, it in enumerate(items, 1):
            f.write(f"{i}. {it['title']}\n")
            f.write(f"   Link: {it['link']}\n")
            if it.get("abstract"):
                f.write(f"   Abstract: {it['abstract']}\n")
            f.write("\n")
    return path_jsonl, path_md


def build_prompt(items, keywords):
    lines = []
    lines.append("You are a very professional research assistant in MIT doing research of battery materials simulation researches.")
    if keywords:
        lines.append(f"First, select only the papers relevant to these keywords: {', '.join(keywords)}.")
    else:
        lines.append("Summarize the following papers.")
    lines.append("For the selected papers, produce:")
    lines.append("- Title")
    lines.append("- 2 sentences shortly summary in your own words")
    lines.append("- Very short!!! Key insights (bullet points: methods, findings, limitations, potential applications)")
    lines.append("- Direct link")
    lines.append("")
    lines.append("Then propose exactly and very shortly!!! FIVE novel research ideas I could explore next, each including:")
    lines.append("- Idea title")
    lines.append("- Rationale (why interesting/important)")
    lines.append("- Feasibility (data, method, risks)")
    lines.append("- Potential impact")
    lines.append("")
    lines.append("Return the full response in clear Markdown with headings:")
    lines.append("## Selected Papers and Summaries")
    lines.append("## Five New Research Ideas")
    lines.append("")
    lines.append("Papers to consider:")
    for i, it in enumerate(items, 1):
        lines.append(f"{i}. Title: {it.get('title','')}")
        lines.append(f"   Link: {it.get('link','')}")
        if it.get("abstract"):
            lines.append(f"   Abstract: {it['abstract']}")
        lines.append("")
    return "\n".join(lines)


def run_cli(prompt_text, tag):
    prompt_file = os.path.join(DATA_DIR, f"prompt_{tag}.txt")
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt_text)
    if CLI_CMD=="claude":
        response = client.messages.create(
            model=CLI_MODEL,
            max_tokens=10000,
            temperature=MODEL_TEMPERATURE,           
            messages=[
                {"role": "user", "content": prompt_text}
            ]
        )
        output = response.content[0].text.strip()
        md_path = os.path.join(DATA_DIR, f"claude_summary_{tag}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(output)
    
    if CLI_CMD=="gemini":
        prompt_file = os.path.join(DATA_DIR, f"prompt_{tag}.txt")
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt_text)
        cmd = [CLI_MODEL, "-m", CLI_MODEL]
        result = subprocess.run(cmd, input=prompt_text, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Gemini CLI failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
        output = result.stdout.strip()
        md_path = os.path.join(DATA_DIR, f"gemini_summary_{tag}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(output)

    return output, md_path

def render_html_report(tag, keywords, items, gemini_markdown, html_path):
    css = """
    :root {
        --bg: #0f172a;
        --panel: #111827;
        --text: #e5e7eb;
        --muted: #9ca3af;
        --accent: #34d399;
        --accent2: #60a5fa;
        --accent3: #f472b6;
    }
    * { box-sizing: border-box; }
    body {
        margin: 0; padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: var(--text); background: linear-gradient(135deg, #0f172a 0%, #1f2937 100%);
    }
    header {
        padding: 24px 32px;
        background: linear-gradient(90deg, rgba(52,211,153,0.15), rgba(96,165,250,0.15));
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    .title {
        font-size: 24px; font-weight: 700; letter-spacing: 0.3px;
    }
    .subtitle {
        color: var(--muted); margin-top: 6px;
    }
    .container { padding: 24px; }
    .panel {
        background: rgba(17,24,39,0.7);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px; padding: 20px; margin-bottom: 20px;
        backdrop-filter: blur(4px);
    }
    .badge {
        display: inline-block; background: rgba(52,211,153,0.15); color: var(--accent);
        border: 1px solid rgba(52,211,153,0.4); border-radius: 999px;
        padding: 6px 10px; font-size: 12px; margin-right: 8px;
    }
    .list-item { margin-bottom: 12px; }
    .list-item .title { color: var(--accent2); font-weight: 600; }
    .list-item a { color: var(--accent3); text-decoration: none; }
    .list-item a:hover { text-decoration: underline; }
    .md {
        white-space: pre-wrap;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        font-size: 14px;
        line-height: 1.5;
    }
    footer {
        color: var(--muted);
        padding: 16px 24px; text-align: right;
        border-top: 1px solid rgba(255,255,255,0.08);
    }
    """
    items_html = []
    for it in items:
        t = (it.get("title") or "").replace("<", "&lt;").replace(">", "&gt;")
        l = (it.get("link") or "")
        a = (it.get("abstract") or "").replace("<", "&lt;").replace(">", "&gt;")
        items_html.append(f"""
        <div class="list-item">
            <div class="title">{t}</div>
            <div><a href="{l}" target="_blank" rel="noopener noreferrer">{l}</a></div>
            {"<div class='abstract'>"+a+"</div>" if a else ""}
        </div>
        """)
    items_block = "\n".join(items_html)
    kw_badges = "".join([f'<span class="badge">{k}</span>' for k in keywords]) if keywords else '<span class="badge">No keywords</span>'
    gm = gemini_markdown.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    html = f"""
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width,initial-scale=1" />
        <title>Scholar Summary Report - {tag}</title>
        <style>{css}</style>
    </head>
    <body>
        <header>
            <div class="title">Scholar Summary Report</div>
            <div class="subtitle">Date: {tag}</div>
            <div class="subtitle">Keywords: {kw_badges}</div>
        </header>
        <div class="container">
            <div class="panel">
                <h2 style="margin-top:0;">Extracted Items (Preview)</h2>
                {items_block if items_block else "<em>No items extracted.</em>"}
            </div>
            <div class="panel">
                <h2 style="margin-top:0;">Gemini Output</h2>
                <div class="md">{gm}</div>
            </div>
        </div>
        <footer>
            Generated by Gmail IMAP + Gemini CLI
        </footer>
    </body>
    </html>
    """
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html_path


def send_report_email(summary_path, tag):
    """
    Send the generated AI summary report via email

    Args:
        summary_path (str): Path to the summary file (claude_summary_*.md or gemini_summary_*.md)
        tag (str): Date tag for the report (YYYY-MM-DD format)

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not ENABLE_EMAIL_SENDING:
        return False  # Silent fail - email sending disabled

    if not REPORT_RECEIVER_EMAIL or REPORT_RECEIVER_EMAIL == "your.receiver@example.com":
        return False  # Silent fail - recipient not configured

    if not os.path.exists(summary_path):
        return False  # Silent fail - file not found

    # Use SMTP_PASSWORD if set, otherwise fall back to IMAP_PASSWORD
    password = SMTP_PASSWORD if SMTP_PASSWORD else IMAP_PASSWORD

    if not password:
        return False  # Silent fail - no password configured

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = REPORT_RECEIVER_EMAIL
    msg['Subject'] = f"AI4GS Research Report - {tag}"

    # Professional email body
    body = f"""Hi, 

Please find attached the AI-generated research report for your recent Google Scholar alerts.

Report Date: {tag}
Keywords: {', '.join(KEYWORDS[:4])}{'...' if len(KEYWORDS) > 4 else ''}

- Generated by AI4GS Research System.
    """

    msg.attach(MIMEText(body, 'plain'))

    # Attach the summary file
    with open(summary_path, 'r', encoding='utf-8') as f:
        attachment = MIMEBase('text', 'plain')
        attachment.set_payload(f.read())
        encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename= "{os.path.basename(summary_path)}"'
        )
        msg.attach(attachment)

    # Try different connection methods
    connection_methods = [
        {
            'name': 'SSL (Port 465)',
            'server': 'smtp.gmail.com',
            'port': 465,
            'use_tls': False,
            'use_ssl': True
        },
        {
            'name': 'STARTTLS (Port 587)',
            'server': SMTP_SERVER,
            'port': SMTP_PORT,
            'use_tls': True,
            'use_ssl': False
        },
        {
            'name': 'STARTTLS (Port 25)',
            'server': SMTP_SERVER,
            'port': 25,
            'use_tls': True,
            'use_ssl': False
        }
    ]

    for method in connection_methods:
        try:
            if method['use_ssl']:
                # Try SSL connection
                server = smtplib.SMTP_SSL(method['server'], method['port'], timeout=30)
                server.login(EMAIL_ADDRESS, password)
                server.send_message(msg)
                server.quit()
            else:
                # Try STARTTLS connection
                server = smtplib.SMTP(method['server'], method['port'], timeout=30)
                server.ehlo()
                if method['use_tls']:
                    server.starttls()
                    server.ehlo()
                server.login(EMAIL_ADDRESS, password)
                server.send_message(msg)
                server.quit()

            # Success message handled by main process
            return True

        except smtplib.SMTPAuthenticationError:
            # Silently fail authentication - main process will handle notification
            break
        except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError, Exception):
            if method == connection_methods[-1]:  # Last method to try
                # Silently fail all attempts - main process will handle notification
                pass
            continue  # Try next method

    return False
