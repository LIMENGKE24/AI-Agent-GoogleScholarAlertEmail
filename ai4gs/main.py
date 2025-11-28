import os
import sys
import argparse
from datetime import datetime

# Use relative imports for package compatibility
try:
    from .config import ALERT_SENDERS, KEYWORDS, TODAY_ONLY, RECENT_COUNT, REPORT_RECEIVER_EMAIL, DATA_DIR
    from .utils import (
        connect_imap_gmail, find_all_mail_mailbox, safe_select,
        get_recent_uids, fetch_header, normalize_from, is_today,
        fetch_body_html, extract_items_from_html,
        save_items, keyword_filter, build_prompt,
        run_cli, send_report_email, convert_md_to_html
    )
except ImportError:
    # Fallback for running script directly
    from config import ALERT_SENDERS, KEYWORDS, TODAY_ONLY, RECENT_COUNT, REPORT_RECEIVER_EMAIL, DATA_DIR
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
    print("      Version 0.1.0 • Professional Research Automation • Build 2025.11\n")

def print_status(step, message, status="INFO"):
    # All indicators have exactly 6 characters for consistent alignment
    indicators = {"INFO": "[INFO]", "SUCCESS": "[OK]  ", "WARNING": "[WARN]", "ERROR": "[ERROR]", "PROCESS": "[PROC]"}
    indicator = indicators.get(status, "[INFO]")
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {indicator} {step.ljust(25)} │ {message}")

def init_config():
    """Initialize configuration by creating a .env file."""
    print_status("INIT", "Initializing AI4GS configuration...", "PROCESS")
    
    if os.path.exists(".env"):
        overwrite = input("A .env file already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print_status("INIT", "Configuration initialization cancelled.", "WARNING")
            return

    print("\nPlease provide the following configuration details:")
    
    email = input("Gmail Address: ").strip()
    password = input("Gmail App Password (not login password): ").strip()
    api_key = input("Anthropic API Key: ").strip()
    receiver = input(f"Report Receiver Email [{email}]: ").strip() or email
    keywords = input("Research Keywords (comma separated): ").strip()
    
    env_content = f"""# AI4GS Configuration
EMAIL_ADDRESS={email}
IMAP_PASSWORD={password}
ANTHROPIC_API_KEY={api_key}

# Report Settings
REPORT_RECEIVER_EMAIL={receiver}
KEYWORDS={keywords}

# Advanced Settings (Defaults)
# RECENT_COUNT=10
# TODAY_ONLY=False
# CLI_CMD=claude
# CLI_MODEL=claude-sonnet-4-5-20250929
# MODEL_TEMPERATURE=0.2
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
        
    print_status("INIT", "Configuration saved to .env file.", "SUCCESS")
    print_status("INIT", "You can now run 'ai4gs run' to start the research agent.", "INFO")

def run_research():
    display_header()
    print_status("INITIALIZATION", "Starting AI4GS Research System...", "INFO")

    try:
        M = connect_imap_gmail()
    except Exception as e:
        print_status("CONNECTION_ERROR", f"Failed to connect: {str(e)}", "ERROR")
        print_status("HINT", "Run 'ai4gs init' to configure your credentials.", "INFO")
        return

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
        html_path = os.path.join(DATA_DIR, f"ai4gs_research_report_{tag}.html")
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

def clean_output():
    """Clean up the output directory."""
    if not os.path.exists(DATA_DIR):
        print_status("CLEAN", f"Directory {DATA_DIR} does not exist.", "WARNING")
        return

    confirm = input(f"Are you sure you want to delete all files in {DATA_DIR}? (y/N): ").strip().lower()
    if confirm != 'y':
        print_status("CLEAN", "Operation cancelled.", "INFO")
        return

    count = 0
    for filename in os.listdir(DATA_DIR):
        file_path = os.path.join(DATA_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
                count += 1
        except Exception as e:
            print_status("CLEAN", f"Failed to delete {file_path}. Reason: {e}", "ERROR")
    
    print_status("CLEAN", f"Successfully deleted {count} files from {DATA_DIR}.", "SUCCESS")

def test_email_config():
    """Send a test email to verify configuration."""
    print_status("TEST", "Sending test email...", "PROCESS")
    try:
        # Create a dummy file for testing
        test_file = os.path.join(DATA_DIR, "test_email.txt")
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(test_file, "w") as f:
            f.write("This is a test email from AI4GS.")
        
        success = send_report_email(test_file, "TEST-EMAIL")
        
        if success:
            print_status("TEST", f"Test email sent successfully to {REPORT_RECEIVER_EMAIL}", "SUCCESS")
        else:
            print_status("TEST", "Failed to send test email. Check your credentials.", "ERROR")
            
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
            
    except Exception as e:
        print_status("TEST", f"Error sending test email: {str(e)}", "ERROR")

def main():
    parser = argparse.ArgumentParser(description="AI4GS: AI-Powered Google Scholar Assistant")
    parser.add_argument("-v", "--version", action="version", version="ai4gs 0.1.0")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # 'init' command
    init_parser = subparsers.add_parser("init", help="Initialize configuration (.env file)")
    
    # 'run' command
    run_parser = subparsers.add_parser("run", help="Run the research agent")
    
    # 'clean' command
    clean_parser = subparsers.add_parser("clean", help="Clean up the output directory")
    
    # 'test-email' command
    test_email_parser = subparsers.add_parser("test-email", help="Send a test email to verify configuration")
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_config()
    elif args.command == "run":
        run_research()
    elif args.command == "clean":
        clean_output()
    elif args.command == "test-email":
        test_email_config()
    else:
        # Default behavior if no command is provided (or just 'ai4gs')
        if len(sys.argv) == 1:
            parser.print_help()
        else:
            parser.print_help()

if __name__ == "__main__":
    main()

