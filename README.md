# 🚀 Auto_Mail

Automated, personalized bulk email dispatcher powered by Python and Gmail SMTP. 

Built for developers, job seekers, and founders who need reliable, personalized outreach directly through their own Gmail account without expensive third-party SaaS subscriptions.

---

## ✨ Features

- **Zero External Dependencies**: Built entirely with Python's standard library (`smtplib`, `email`, `ssl`, etc.) — no `pip install` required.
- **Dual HTML & Plaintext Templates**: Supports responsive HTML emails ([template.html](template.html)) with a clean plain-text fallback ([template.txt](template.txt)).
- **Dynamic Variable Substitution**: Automatically personalizes each email with `{name}`, `{company_phrase}`, `{sender_name}`, `{contact_number}`, and `{sender_email}`.
- **Automatic Resume & File Attachment**: Seamlessly attaches your PDF resume ([Bashetty-Sanjay.pdf](Bashetty-Sanjay.pdf)) or custom documents using standard RFC-compliant MIME packaging.
- **Multiple Recipient Formats**: Works out-of-the-box with both `.txt` (comma-separated: `email, Name, Company`) and `.csv` files.
- **Safe Dry-Run Preview**: Preview formatted emails, subjects, and attachment status in your terminal before sending.
- **Single Test Mode**: Verify inbox deliverability and attachment integrity with `--test your_email@gmail.com`.
- **Rate-Limiting & Auto-Reconnect**: Configurable delays between sends to respect Gmail sending limits, with automatic reconnect upon connection drops.
- **Audit Logging**: Automatically records every dispatched email's timestamp, status (`SUCCESS` / `FAILED`), and error details in `sent_log.csv`.

---

## 📁 Repository Structure

```text
Auto_Mail/
├── send_bulk.py          # Core bulk dispatch engine
├── template.html         # Responsive HTML email template
├── template.txt          # Clean plain-text fallback template
├── Bashetty-Sanjay.pdf   # Resume PDF attachment
├── recipients.txt        # Recipient list (txt format: email, name, company)
├── recipients.csv        # Recipient list (csv format: email, name, company, ...)
├── .env.example          # Environment variables template
├── .gitignore            # Git exclusion rules (protects credentials & logs)
└── README.md             # Documentation
```

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.8+ installed.
- A Google Account with **2-Step Verification** enabled.

### 2. Configure Gmail App Password
1. Navigate to [Google Account Security](https://myaccount.google.com/security).
2. Under **How you sign in to Google**, ensure **2-Step Verification** is turned on.
3. Search for **App passwords** or go to [App passwords](https://myaccount.google.com/apppasswords).
4. Enter an app name (e.g., `Auto Mail`) and click **Create**.
5. Copy the generated 16-character password (e.g., `xxxx xxxx xxxx xxxx`).

### 3. Setup Environment Variables
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
Open `.env` and fill in your details:
```env
# Your Gmail address
GMAIL_USER=your_email@gmail.com

# Your 16-character Google App Password
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Name shown to recipients as the sender
SENDER_NAME=Sanjay Bashetty

# Sender contact email displayed in signature
SENDER_EMAIL=bashettysanjay@gmail.com

# Sender contact phone number displayed in signature
CONTACT_NUMBER=+91 9866347550

# Default Email Subject (supports {name} placeholder)
EMAIL_SUBJECT=Inquiry About Entry-Level Opportunities
```

> ⚠️ **Security Notice**: `.env` and `sent_log.csv` are included in `.gitignore` to prevent leaking private credentials or recipient logs. Never remove them from `.gitignore`.

---

## 👥 Managing Recipients

### Option A: `recipients.txt` (Recommended)
Add your recipients (one per line):
```text
# Format: email, First Name, Company
akanksha.puri@sourcefuse.com, Akanksha, SourceFuse Technologies
akanksha.sogani@perennialsys.com, Akanksha, Perennial Systems
recruiter@techcorp.com, Sarah, TechCorp
```
*(If name or company is omitted, it automatically falls back to `Dear Hiring Team,` and `in your organization`).*

### Option B: `recipients.csv`
Provide a standard `.csv` file:
```csv
email,name,company
akanksha.puri@sourcefuse.com,Akanksha,SourceFuse Technologies
akanksha.sogani@perennialsys.com,Akanksha,Perennial Systems
```

---

## 🛠️ Usage & Commands

### 1. Dry Run (Preview without sending)
Preview the personalized subject and body for the first recipients in your terminal:
```powershell
python send_bulk.py --dry-run
```

### 2. Send a Single Test Email
Verify formatting and check inbox placement before broadcasting:
```powershell
python send_bulk.py --test your_personal_email@gmail.com
```

### 3. Dispatch Bulk Emails
```powershell
python send_bulk.py
```
*You will be prompted with a confirmation summary (sender, count, delay, attachment) before dispatch starts.*

### 4. Skip Confirmation Prompt
```powershell
python send_bulk.py --yes
```

---

## ⚙️ CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `--dry-run` | Preview messages in console without sending | `False` |
| `--test <email>` | Send a single test email to the specified address | `None` |
| `--file <path>` | Path to custom `.txt` or `.csv` recipient file | `recipients.txt` |
| `--delay <seconds>` | Sleep delay between consecutive sends | `2.0` |
| `--subject "<text>"` | Override default email subject | From `.env` |
| `--attach "<path>"` | Path to custom file attachment | `Bashetty-Sanjay.pdf` |
| `--yes`, `-y` | Skip confirmation prompt and start dispatch immediately | `False` |

### Example with Custom Options:
```powershell
python send_bulk.py --file leads.csv --delay 3.0 --subject "Inquiry - Sanjay Bashetty" --attach "Bashetty-Sanjay.pdf"
```

---

## 📊 Delivery Logs

After each run, status logs are recorded in `sent_log.csv`:
```csv
Timestamp,Recipient,Status,Details
2026-09-18 01:16:01,user@example.com,SUCCESS,Test email
2026-09-18 01:32:19,akanksha.puri@sourcefuse.com,SUCCESS,
```

---

## 📄 License

MIT License.
