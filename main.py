import os
from datetime import datetime

from config import ALERT_SENDERS, KEYWORDS, TODAY_ONLY, RECENT_COUNT, REPORT_RECEIVER_EMAIL
from utils import (
    connect_imap_gmail, find_all_mail_mailbox, safe_select,
    get_recent_uids, fetch_header, normalize_from, is_today,
    fetch_body_html, extract_items_from_html,
    save_items, keyword_filter, build_prompt,
    run_cli, send_report_email, convert_md_to_html
)

def display_header():
    print("\n╔" + "═"*75 + "╗")
    print("║" + " "*27 + "AI4GS RESEARCH SYSTEM" + " "*27 + "║")
    print("╠" + "═"*75 + "╣")
    print("║" + " "*20 + "    _    ___ _  _    ____ ____              " + " "*11 + "║")
    print("║" + " "*20 + "   / \\  |_ _| || |  / ___/ ___|             " + " "*11 + "║")
    print("║" + " "*20 + "  / _ \\  | || || |_| |  _\\___ \\              " + " "*10 + "║")
    print("║" + " "*20 + " / ___ \\ | ||__   _| |_| |___) |             " + " "*10 + "║")
    print("║" + " "*20 + "/_/   \\_\\___|  |_|  \\____|____/              " + " "*10 + "║")
    print("║" + " "*18 + "AI-POWERED GOOGLE SCHOLAR ASSISTANT" + " "*22 + "║")
    print("╚" + "═"*75 + "╝")
    print("      Version 0.0.1 • Professional Research Automation • Build 2025.11\n")

display_header()
                                      
def print_status(step, message, status="INFO"):
    # All indicators have exactly 6 characters for consistent alignment
    indicators = {"INFO": "[INFO]", "SUCCESS": "[OK]  ", "WARNING": "[WARN]", "ERROR": "[ERROR]", "PROCESS": "[PROC]"}
    indicator = indicators.get(status, "[INFO]")
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {indicator} {step.ljust(25)} │ {message}")

def main():
    print_status("INITIALIZATION", "Starting AI4GS Research System...", "INFO")

    M = connect_imap_gmail()
    try:
        print_status("EMAIL_CONNECTION", "Establishing secure connection to Gmail IMAP server...", "PROCESS")
        mailbox = find_all_mail_mailbox(M) or "INBOX"
        selected = safe_select(M, mailbox)
        print_status("MAILBOX_SELECTED", f"Successfully connected to: {selected}", "SUCCESS")

        print_status("EMAIL_RETRIEVAL", f"Searching recent {RECENT_COUNT} messages...", "PROCESS")
        uids = get_recent_uids(M, max_count=RECENT_COUNT)
        if not uids:
            print_status("NO_MESSAGES", "No messages found in mailbox", "WARNING")
            return

        print_status("FILTERING", f"Filtering {len(uids)} messages for Scholar Alerts...", "PROCESS")
        matched_uids = []
        for uid in reversed(uids):
            hdr = fetch_header(M, uid)
            if not hdr:
                continue
            addr = normalize_from(hdr["from"])
            if addr in ALERT_SENDERS and (not TODAY_ONLY or is_today(hdr["dt"])):
                matched_uids.append(uid)

        if not matched_uids:
            print_status("NO_MATCHES", "No Scholar Alert messages found matching criteria", "WARNING")
            return

        print_status("EXTRACTION", f"Processing {len(matched_uids)} Scholar Alert messages...", "PROCESS")
        items = []
        for i, uid in enumerate(matched_uids, 1):
            print(f"\r[{'█' * min(20, int(20*i/len(matched_uids)))}{'░' * max(0, 20-int(20*i/len(matched_uids)))}] {i}/{len(matched_uids)} messages", end="", flush=True)
            html = fetch_body_html(M, uid)
            if not html:
                continue
            items.extend(extract_items_from_html(html))
        print()  # New line after progress bar

        print_status("DEDUPLICATION", "Removing duplicate research papers...", "PROCESS")
        uniq = []
        seen = set()
        for it in items:
            key = (it.get("title"), it.get("link"))
            if key not in seen:
                seen.add(key)
                uniq.append(it)

        if len(uniq) >= 2:
            uniq = uniq[:-2]

        tag = datetime.now().strftime("%Y-%m-%d")
        save_items(uniq, tag)
        print_status("DATA_SAVED", f"Successfully saved {len(uniq)} unique papers to database", "SUCCESS")

        print_status("KEYWORD_FILTERING", f"Applying research keyword filters...", "PROCESS")
        filtered = keyword_filter(uniq, KEYWORDS)
        if not filtered:
            print_status("NO_MATCHES", f"No papers matched research keywords: {', '.join(KEYWORDS[:3])}...", "WARNING")
            return

        print_status("AI_PROCESSING", f"Generating AI summary for {len(filtered)} relevant papers...", "PROCESS")
        prompt_text = build_prompt(filtered, KEYWORDS)
        out_summary,summary_path = run_cli(prompt_text, tag)
        print_status("AI_COMPLETE", f"AI analysis completed successfully", "SUCCESS")

        print_status("HTML_GENERATION", "Creating professional HTML report...", "PROCESS")
        html_path = os.path.join("Summarize_Output", f"ai4gs_research_report_{tag}.html")
        convert_md_to_html(summary_path, html_path, tag, KEYWORDS, filtered)
        print_status("HTML_COMPLETE", "Professional HTML report generated successfully", "SUCCESS")

        print_status("EMAIL_DISPATCH", "Delivering research report to recipient...", "PROCESS")
        email_success = send_report_email(html_path, tag)

        if email_success:
            print_status("EMAIL_SENT", f"Research report delivered to {REPORT_RECEIVER_EMAIL}", "SUCCESS")
        else:
            print_status("EMAIL_FAILED", "Email delivery failed - report saved locally", "WARNING")

        print_status("COMPLETION", f"Research pipeline completed successfully • {len(filtered)} papers processed", "SUCCESS")

    finally:
        try:
            M.close()
        except:
            pass
        M.logout()


if __name__ == "__main__":
    main()
