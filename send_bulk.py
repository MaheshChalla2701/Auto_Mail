#!/usr/bin/env python3
"""
FIZI Bulk Email Automation Tool
-------------------------------
Sends personalized bulk emails using Gmail SMTP and an App Password.
Features:
- Reads recipients from a CSV file (recipients.csv).
- Supports HTML and plain-text fallback templates.
- Supports any custom CSV column as template variables (e.g. {name}, {custom_note}).
- Dry-run mode for previewing emails before sending.
- Test mode (--test email@domain.com) to send a single test email.
- Configurable delay between sends to prevent Gmail rate limits.
- Writes full delivery status to sent_log.csv.
"""

import os
import sys
import csv
import re
import time
import ssl
import smtplib
import argparse
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from pathlib import Path

# Fix Windows console UTF-8 output if supported
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Paths
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
RECIPIENTS_TXT_PATH = BASE_DIR / "recipients.txt"
HTML_TEMPLATE_PATH = BASE_DIR / "template.html"
LOGO_PATH = BASE_DIR / "fizi_logo.png"
DEFAULT_DECK_PATH = BASE_DIR / "FIZI ppt fin.pptx"
LOG_PATH = BASE_DIR / "sent_log.csv"

# Email validation regex
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def load_env_file(env_file_path: Path):
    """Manually parse .env file to avoid external library dependency."""
    env_vars = {}
    if not env_file_path.exists():
        # Also check parent directory if not found locally
        parent_env = env_file_path.parent.parent.parent / ".env"
        if parent_env.exists():
            env_file_path = parent_env
        else:
            return env_vars

    with open(env_file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                env_vars[key] = val
    return env_vars


def get_config():
    """Load configuration from environment or .env file."""
    env_vars = load_env_file(ENV_PATH)
    
    gmail_user = os.getenv("GMAIL_USER") or env_vars.get("GMAIL_USER")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD") or env_vars.get("GMAIL_APP_PASSWORD")
    sender_name = os.getenv("SENDER_NAME") or env_vars.get("SENDER_NAME") or "FIZI Team"
    email_subject = os.getenv("EMAIL_SUBJECT") or env_vars.get("EMAIL_SUBJECT") or "Message from {sender_name}"

    # Strip spaces from 16-character app password if present
    if gmail_pass:
        gmail_pass = gmail_pass.replace(" ", "")

    return {
        "user": gmail_user,
        "password": gmail_pass,
        "sender_name": sender_name,
        "default_subject": email_subject
    }


def load_recipients_txt(txt_path: Path):
    """Read recipients from a .txt file (one email per line, or 'email, name', or 'Name <email>')."""
    if not txt_path.exists():
        print(f"Error: Recipients file not found at {txt_path}")
        return []

    recipients = []
    with open(txt_path, mode="r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            name = ""
            custom_note = ""
            email = ""

            # Check format: Name <email@example.com>
            angle_match = re.search(r"^(.*?)\s*<([^>]+)>$", line)
            if angle_match:
                name = angle_match.group(1).strip()
                email = angle_match.group(2).strip()
            elif "," in line:
                # Delimited format: email, name, custom_note
                parts = [p.strip() for p in line.split(",")]
                email = parts[0]
                if len(parts) > 1:
                    name = parts[1]
                if len(parts) > 2:
                    custom_note = ",".join(parts[2:]).strip()
            else:
                email = line

            if not email or not EMAIL_REGEX.match(email):
                print(f"[Line {line_num}] Skipping invalid or empty email: '{email}'")
                continue

            # Skip placeholder examples
            if email in ("test1@example.com", "test2@example.com", "user@example.com", "user1@gmail.com"):
                continue

            recipients.append({
                "email": email,
                "name": name,
                "custom_note": custom_note
            })

    return recipients


def load_recipients_csv(csv_path: Path):
    """Read recipients and personalization fields from CSV."""
    if not csv_path.exists():
        print(f"Error: Recipients file not found at {csv_path}")
        return []

    recipients = []
    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "email" not in [col.strip().lower() for col in reader.fieldnames]:
            print("Error: CSV must contain an 'email' column header.")
            return []

        # Map actual header names to normalized lower-case for easy access
        col_map = {col.strip().lower(): col for col in reader.fieldnames}
        email_col = col_map["email"]

        for row_num, row in enumerate(reader, start=2):
            raw_email = row.get(email_col, "").strip()
            if not raw_email or not EMAIL_REGEX.match(raw_email):
                print(f"[Line {row_num}] Skipping invalid or empty email: '{raw_email}'")
                continue
            
            # Skip placeholder examples
            if raw_email in ("test1@example.com", "test2@example.com", "user@example.com"):
                continue

            cleaned_row = {k.strip(): v.strip() for k, v in row.items()}
            recipients.append(cleaned_row)

    return recipients


def load_recipients(file_path: Path):
    """Load recipients automatically detecting .txt or .csv format."""
    if str(file_path).lower().endswith(".txt"):
        return load_recipients_txt(file_path)
    return load_recipients_csv(file_path)



def format_template(template_str: str, data: dict) -> str:
    """Safely replace only {var_name} placeholders without clashing with CSS { } blocks."""
    def replacer(match):
        key = match.group(1)
        if key in data:
            return str(data[key])
        return match.group(0)

    return re.sub(r"\{([a-zA-Z0-9_]+)\}", replacer, template_str)


def create_message(sender_email, sender_name, recipient_email, subject, body_txt, body_html, attachment_path=None, logo_path=None):
    """Build an email message with embedded inline logo and optional attachments."""
    if attachment_path and Path(attachment_path).exists():
        root_msg = MIMEMultipart("mixed")
        related_part = MIMEMultipart("related")
        root_msg.attach(related_part)
    else:
        root_msg = MIMEMultipart("related")
        related_part = root_msg

    root_msg["From"] = f"{sender_name} <{sender_email}>"
    root_msg["To"] = recipient_email
    root_msg["Subject"] = subject

    # Alternative text & HTML
    alt_part = MIMEMultipart("alternative")
    if body_txt:
        alt_part.attach(MIMEText(body_txt, "plain", "utf-8"))
    if body_html:
        alt_part.attach(MIMEText(body_html, "html", "utf-8"))
    related_part.attach(alt_part)

    # Inline Logo (<img src="cid:fizi_logo">)
    if logo_path and Path(logo_path).exists():
        with open(logo_path, "rb") as f:
            img = MIMEImage(f.read())
            img.add_header("Content-ID", "<fizi_logo>")
            img.add_header("Content-Disposition", "inline", filename="fizi_logo.png")
            related_part.attach(img)

    # Optional file attachment
    if attachment_path and Path(attachment_path).exists():
        filepath = Path(attachment_path)
        with open(filepath, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {filepath.name}",
        )
        root_msg.attach(part)

    return root_msg


def append_log(recipient_email, status, message=""):
    """Log email dispatch results to sent_log.csv."""
    write_header = not LOG_PATH.exists()
    with open(LOG_PATH, mode="a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["Timestamp", "Recipient", "Status", "Details"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            recipient_email,
            status,
            message
        ])


def main():
    parser = argparse.ArgumentParser(description="FIZI Automated Bulk Email Sender")
    parser.add_argument("--dry-run", action="store_true", help="Preview generated emails without sending.")
    parser.add_argument("--test", type=str, metavar="EMAIL", help="Send a single test email to the specified address.")
    parser.add_argument("--file", type=str, help="Path to recipients file (.txt or .csv). Defaults to recipients.txt (if present) or recipients.csv.")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay in seconds between sends (default: 2.0s).")
    parser.add_argument("--attach", type=str, help="Path to a file to attach to every email.")
    parser.add_argument("--subject", type=str, help="Override subject line.")
    args = parser.parse_args()

    print("=" * 60)
    print("  FIZI Bulk Email Automation Tool")
    print("=" * 60)

    # 1. Load Configurations
    config = get_config()

    if not config["user"] or not config["password"]:
        print("\n[!] Configuration missing:")
        if not config["user"]:
            print("  - GMAIL_USER is missing in .env")
        if not config["password"]:
            print("  - GMAIL_APP_PASSWORD is missing in .env")
        print("\nPlease copy .env.example to .env")
        print("and fill in your Gmail address and 16-character App Password.\n")
        if not args.dry_run:
            sys.exit(1)

    # 2. Load Templates
    raw_html = ""
    raw_txt = ""
    if HTML_TEMPLATE_PATH.exists():
        raw_html = HTML_TEMPLATE_PATH.read_text(encoding="utf-8")
        # Generate clean plain-text fallback by removing style blocks and tags
        clean_text = re.sub(r"(?is)<style.*?>.*?</style>", "", raw_html)
        clean_text = re.sub(r"<[^>]+>", "", clean_text)
        raw_txt = re.sub(r"\n\s*\n+", "\n\n", clean_text).strip()

    if not raw_html:
        print("Error: No template found. Please create template.html")
        sys.exit(1)

    subject_template = args.subject or config["default_subject"]

    # Determine attachment (custom --attach or default FIZI pitch deck)
    attachment_path = None
    if args.attach:
        attachment_path = args.attach
    elif DEFAULT_DECK_PATH.exists():
        attachment_path = str(DEFAULT_DECK_PATH)

    # 3. Handle Test Mode
    if args.test:
        test_email = args.test.strip()
        if not EMAIL_REGEX.match(test_email):
            print(f"Error: Invalid test email address '{test_email}'")
            sys.exit(1)

        print(f"\n[Mode: Single Test Email] Target: {test_email}")
        if attachment_path:
            print(f"Attached Deck: {Path(attachment_path).name}")

        test_data = {
            "email": test_email,
            "name": "Tester",
            "custom_note": "This is a test run to verify the layout and delivery.",
            "sender_name": config["sender_name"]
        }

        subj = format_template(subject_template, test_data)
        body_h = format_template(raw_html, test_data) if raw_html else None
        body_t = format_template(raw_txt, test_data) if raw_txt else None

        msg = create_message(
            config["user"],
            config["sender_name"],
            test_email,
            subj,
            body_t,
            body_h,
            attachment_path,
            logo_path=LOGO_PATH
        )

        if args.dry_run:
            print("[Dry-run] Test email created successfully. Not sent.")
            return

        print(f"Connecting to Gmail SMTP server (smtp.gmail.com)...")
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(config["user"], config["password"])
                server.send_message(msg)
            append_log(test_email, "SUCCESS", "Test email")
            print(f"[OK] Success! Test email delivered to {test_email}")
        except Exception as e:
            append_log(test_email, "FAILED", str(e))
            print(f"[X] Failed to send test email: {e}")
        return

    # 4. Load Recipients for Bulk Send
    if args.file:
        recipients_file = Path(args.file)
    else:
        recipients_file = RECIPIENTS_TXT_PATH

    recipients = load_recipients(recipients_file)
    if not recipients:
        print(f"\nNo valid recipients found in {recipients_file.name} to send.")
        print("Please add your recipients (one per line) to recipients.txt")
        sys.exit(0)

    print(f"\nLoaded {len(recipients)} recipient(s) from {recipients_file.name}")

    # 5. Dry-run Mode
    if args.dry_run:
        print("\n--- [DRY RUN PREVIEW (First 2 Recipients)] ---")
        for i, rec in enumerate(recipients[:2]):
            context_data = {**rec, "sender_name": config["sender_name"]}
            if "name" not in context_data or not context_data["name"]:
                context_data["name"] = "there"
            preview_subject = format_template(subject_template, context_data)
            print(f"\n[#{i+1}] To: {rec.get('email')} | Subject: {preview_subject}")
            if raw_txt:
                preview_body = format_template(raw_txt, context_data)
                print(f"Body snippet:\n{preview_body[:200]}...")
        print("\n--- [DRY RUN COMPLETE: No emails were sent] ---")
        return

    # 6. User Confirmation for Bulk Sending
    print(f"Sender: {config['sender_name']} <{config['user']}>")
    print(f"Recipients count: {len(recipients)}")
    print(f"Delay between sends: {args.delay}s")
    if attachment_path:
        print(f"Attachment (Deck): {Path(attachment_path).name}")

    confirm = input("\nProceed with sending bulk emails now? [y/N]: ").strip().lower()
    if confirm not in ("y", "yes"):
        print("Cancelled by user. No emails were sent.")
        return

    # 7. Connect and Send Bulk Emails
    print("\nConnecting to Gmail SMTP server...")
    sent_count = 0
    fail_count = 0

    context = ssl.create_default_context()

    def connect_smtp():
        s = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context)
        s.login(config["user"], config["password"])
        return s

    try:
        server = connect_smtp()
        print("Authenticated successfully with Gmail.\nStarting dispatch...\n")

        for idx, rec in enumerate(recipients, start=1):
            rec_email = rec["email"]
            context_data = {**rec, "sender_name": config["sender_name"]}
            if "name" not in context_data or not context_data["name"]:
                context_data["name"] = "there"
            if "custom_note" not in context_data:
                context_data["custom_note"] = ""

            subject = format_template(subject_template, context_data)
            body_h = format_template(raw_html, context_data) if raw_html else None
            body_t = format_template(raw_txt, context_data) if raw_txt else None

            msg = create_message(
                sender_email=config["user"],
                sender_name=config["sender_name"],
                recipient_email=rec_email,
                subject=subject,
                body_txt=body_t,
                body_html=body_h,
                attachment_path=attachment_path,
                logo_path=LOGO_PATH
            )

            try:
                server.send_message(msg)
                sent_count += 1
                append_log(rec_email, "SUCCESS")
                print(f"[{idx}/{len(recipients)}] [OK] Sent to: {rec_email}")
            except Exception as send_err:
                print(f"  [!] Connection interrupted ({send_err}). Reconnecting to Gmail...")
                try:
                    server = connect_smtp()
                    server.send_message(msg)
                    sent_count += 1
                    append_log(rec_email, "SUCCESS")
                    print(f"[{idx}/{len(recipients)}] [OK] Sent to: {rec_email} (after reconnect)")
                except Exception as retry_err:
                    fail_count += 1
                    append_log(rec_email, "FAILED", str(retry_err))
                    print(f"[{idx}/{len(recipients)}] [X] Failed for {rec_email}: {retry_err}")

            # Rate limiting sleep between sends
            if idx < len(recipients):
                time.sleep(args.delay)

        try:
            server.quit()
        except Exception:
            pass

    except Exception as conn_err:
        print(f"\n[!] SMTP Connection or Authentication failed: {conn_err}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print(f"Dispatch Finished! Total: {len(recipients)} | Sent: {sent_count} | Failed: {fail_count}")
    print(f"Log saved to: {LOG_PATH.name}")
    print("=" * 60)


if __name__ == "__main__":
    main()
