import pandas as pd
import smtplib
from email.message import EmailMessage
from datetime import datetime
import os

# ======================================
# CONFIG (SENDER / BRAND)
# ======================================
ORG_NAME = os.getenv("ORG_NAME", "Sodbridge")
SENDER_EMAIL = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SHEET_CSV_URL = os.getenv("SHEET_CSV_URL")

LOG_FILE = "sent_log.csv"

# ======================================
# LOAD GOOGLE SHEET
# ======================================
df = pd.read_csv(SHEET_CSV_URL)

today = datetime.today()
current_year = today.year

# ======================================
# LOAD / INIT SEND LOG
# ======================================
if os.path.exists(LOG_FILE):
    sent_log = pd.read_csv(LOG_FILE)
else:
    sent_log = pd.DataFrame(columns=["email", "year"])

def already_sent(email, year):
    return ((sent_log["email"] == email) & (sent_log["year"] == year)).any()

def mark_as_sent(email, year):
    global sent_log
    sent_log = pd.concat(
        [sent_log, pd.DataFrame([{"email": email, "year": year}])],
        ignore_index=True
    )

# ======================================
# EMAIL FUNCTION
# ======================================
def send_email(to_email, subject, body):
    msg = EmailMessage()
    msg["From"] = f"{ORG_NAME} <{SENDER_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.send_message(msg)

# ======================================
# PROCESS BIRTHDAYS
# ======================================
for _, row in df.iterrows():
    dob = pd.to_datetime(row.get("dob"), errors="coerce")
    if pd.isna(dob):
        continue

    if dob.day != today.day or dob.month != today.month:
        continue

    email = row.get("email_address")
    if not email or already_sent(email, current_year):
        continue

    consent = str(row.get("consent", "")).lower()
    if "yes" not in consent:
        continue

    name = row.get("full_name")
    gender = str(row.get("gender", "")).lower()
    organization = row.get("org")

    title = "Mr." if gender == "male" else "Ms."

    subject = "🎉 Happy Birthday!"
    body = f"""
Dear {title} {name},

🎂 Happy Birthday!

Everyone at {ORG_NAME} wishes you a year filled with growth,
success, and happiness. We’re glad to celebrate you today.

Warm regards,
{ORG_NAME} Team
"""

    send_email(email, subject, body)
    mark_as_sent(email, current_year)

    print(f"Birthday email sent to {name} ({email})")

# ======================================
# SAVE SEND LOG
# ======================================
sent_log.to_csv(LOG_FILE, index=False)
