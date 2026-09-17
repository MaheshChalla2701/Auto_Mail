# 🚀 Auto_Mail

Automated, personalized bulk email dispatcher powered by Python and Gmail SMTP. 

Designed for founders, marketers, and developers who need reliable, personalized outreach directly through their own Gmail account without expensive third-party SaaS tools.

---

## ✨ Features

- **Zero External Dependencies**: Built entirely with Python's standard library (smtplib, email, ssl, etc.) — no pip install required.
- **Rich HTML & Plaintext Templates**: Supports beautiful responsive HTML emails with automatic variable replacement (e.g. {name}, {custom_note}).
- **Multiple Recipient Formats**: Works seamlessly with .txt (one per line, comma-separated) and .csv files.
- **Safe Dry-Run Preview**: Preview formatted emails and subjects in the terminal before sending a single message.
- **Single Test Mode**: Test email rendering and inbox deliverability with --test user@example.com.
- **Rate-Limiting & Auto-Reconnect**: Configurable delays between sends to respect Gmail sending limits, with automatic reconnect upon connection drops.
- **Audit Logging**: Automatically records every dispatched email's timestamp, status (SUCCESS / FAILED), and error details in sent_log.csv.
- **Inline Images & Attachments**: Supports CID-embedded logos and file attachments (e.g., presentations, PDFs).

---

## 📁 Repository Structure

`	ext
Auto_Mail/
├── send_bulk.py          # Core bulk dispatch engine
├── template.html         # Responsive HTML email template
├── recipients.txt        # Recipient list (txt or csv)
├── .env.example          # Environment variables template
├── .gitignore            # Git exclusion rules (protects credentials & logs)
├── fizi_logo.png         # Brand logo asset
├── FIZI ppt fin.pptx     # Presentation attachment
├── upload_logo.py        # Cloudinary image upload utility
└── README.md             # Documentation
`

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.8+ installed.
- A Google Account with **2-Step Verification** enabled.

### 2. Configure Gmail App Password
1. Navigate to [Google Account Security](https://myaccount.google.com/security).
2. Under **How you sign in to Google**, ensure **2-Step Verification** is turned on.
3. Search for **App passwords** or go to [App passwords](https://myaccount.google.com/apppasswords).
4. Enter an app name (e.g., Auto Mail) and click **Create**.
5. Copy the generated 16-character password (e.g., xxxx xxxx xxxx xxxx).

### 3. Setup Environment Variables
Copy .env.example to .env:
`powershell
cp .env.example .env
`
Open .env and fill in your details:
`env
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
SENDER_NAME=Your Name or Team
EMAIL_SUBJECT=Connecting with you, {name}
`

> ⚠️ **Security Notice**: .env and sent_log.csv are included in .gitignore to prevent leaking credentials or private recipient logs. Never remove them from .gitignore.

---

## 👥 Managing Recipients

Add your recipient list to ecipients.txt. Supported formats:

`	ext
# Simple email
john@example.com

# Email with Name
sarah@example.com, Sarah

# Email, Name, and Custom Note
alex@example.com, Alex, Loved your keynote at the summit!

# RFC format
"David Miller" <david@example.com>
`

Alternatively, provide any .csv file with an email header (plus optional columns like 
ame, company, etc.):
`csv
email,name,company
alex@example.com,Alex,Acme Corp
`

---

## 🛠️ Usage & Commands

### 1. Dry Run (Preview without sending)
Preview the personalized subject and body for the first recipients in your terminal:
`powershell
python send_bulk.py --dry-run
`

### 2. Send a Single Test Email
Verify formatting and check spam folder placement before broadcasting:
`powershell
python send_bulk.py --test your_personal_email@gmail.com
`

### 3. Dispatch Bulk Emails
`powershell
python send_bulk.py
`
*You will be prompted with a confirmation summary (sender, count, delay, attachment) before dispatch starts.*

---

## ⚙️ CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| --dry-run | Preview messages in console without sending | False |
| --test <email> | Send a single test email | None |
| --file <path> | Path to custom .txt or .csv recipient file | ecipients.txt |
| --delay <seconds> | Sleep delay between consecutive emails | 2.0 |
| --subject "<text>" | Override default email subject (supports {name}) | From .env |
| --attach "<path>" | Path to custom file attachment (PDF, PPTX, etc.) | Default deck if present |

### Example with Custom Options:
`powershell
python send_bulk.py --file investors.csv --delay 3.5 --subject "Quick question for {name}" --attach "reports/q3_summary.pdf"
`

---

## 📊 Delivery Logs

After each run, status logs are appended to sent_log.csv:
`csv
Timestamp,Recipient,Status,Details
2026-09-18 00:35:10,user@example.com,SUCCESS,
2026-09-18 00:35:14,invalid-email,FAILED,550 User not found
`

---

## 📄 License

MIT License. Feel free to modify and adapt for your own workflows!
