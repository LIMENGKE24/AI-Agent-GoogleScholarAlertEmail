from datetime import datetime

from config import ALERT_SENDERS, KEYWORDS, TODAY_ONLY, RECENT_COUNT
from utils import (
    connect_imap_gmail, find_all_mail_mailbox, safe_select,
    get_recent_uids, fetch_header, normalize_from, is_today,
    fetch_body_html, extract_items_from_html,
    save_items, keyword_filter, build_gemini_prompt,
    run_gemini_cli
)

def main():
    M = connect_imap_gmail()
    try:
        mailbox = find_all_mail_mailbox(M) or "INBOX"
        selected = safe_select(M, mailbox)
        print(f"Selected mailbox: {selected}")

        uids = get_recent_uids(M, max_count=RECENT_COUNT)
        if not uids:
            print("No messages found.")
            return

        matched_uids = []
        for uid in reversed(uids):
            hdr = fetch_header(M, uid)
            if not hdr:
                continue
            addr = normalize_from(hdr["from"])
            if addr in ALERT_SENDERS and (not TODAY_ONLY or is_today(hdr["dt"])):
                matched_uids.append(uid)

        if not matched_uids:
            print("No messages from alert senders (or none today).")
            return

        print(f"Found {len(matched_uids)} matching messages. Extracting items...")
        items = []
        for uid in matched_uids:
            html = fetch_body_html(M, uid)
            if not html:
                continue
            items.extend(extract_items_from_html(html))

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
        jpath, mpath = save_items(uniq, tag)
        print(f"Saved {len(uniq)} items to:\n- {jpath}\n- {mpath}")

        filtered = keyword_filter(uniq, KEYWORDS)
        if not filtered:
            print("No items matched your keywords.")
            return

        prompt_text = build_gemini_prompt(filtered, KEYWORDS)
        out_summary = run_gemini_cli(prompt_text, tag)
        print(f"Gemini summary written to: {out_summary}")

    finally:
        try:
            M.close()
        except:
            pass
        M.logout()


if __name__ == "__main__":
    main()
