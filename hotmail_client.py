"""
Hotmail/Outlook Email Client

Connects to Hotmail/Outlook using IMAP (read) and SMTP (send).
Uses Microsoft's mail servers: outlook.office365.com
"""

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import getpass

# Hotmail/Outlook server settings
IMAP_SERVER = "outlook.office365.com"
IMAP_PORT = 993
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587


class HotmailClient:
    def __init__(self, email_address, password):
        self.email_address = email_address
        self.password = password
        self.imap_conn = None
        self.smtp_conn = None

    # -- IMAP (Reading Emails) --

    def connect_imap(self):
        """Connect to Hotmail IMAP server."""
        self.imap_conn = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        self.imap_conn.login(self.email_address, self.password)
        print("Connected to IMAP server.")

    def list_folders(self):
        """List all mailbox folders."""
        status, folders = self.imap_conn.list()
        if status == "OK":
            for folder in folders:
                print(folder.decode())

    def fetch_recent_emails(self, folder="INBOX", count=5):
        """Fetch the most recent emails from a folder."""
        self.imap_conn.select(folder)
        status, messages = self.imap_conn.search(None, "ALL")
        if status != "OK":
            print("No messages found.")
            return []

        msg_ids = messages[0].split()
        recent_ids = msg_ids[-count:] if len(msg_ids) >= count else msg_ids
        emails = []

        for msg_id in reversed(recent_ids):
            status, msg_data = self.imap_conn.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject = _decode_header(msg["Subject"])
            sender = _decode_header(msg["From"])
            date = msg["Date"]

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(
                            part.get_content_charset() or "utf-8", errors="replace"
                        )
                        break
            else:
                body = msg.get_payload(decode=True).decode(
                    msg.get_content_charset() or "utf-8", errors="replace"
                )

            emails.append({
                "subject": subject,
                "from": sender,
                "date": date,
                "body": body,
            })

        return emails

    def disconnect_imap(self):
        """Close the IMAP connection."""
        if self.imap_conn:
            self.imap_conn.logout()
            self.imap_conn = None
            print("Disconnected from IMAP server.")

    # -- SMTP (Sending Emails) --

    def connect_smtp(self):
        """Connect to Hotmail SMTP server."""
        self.smtp_conn = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        self.smtp_conn.ehlo()
        self.smtp_conn.starttls()
        self.smtp_conn.login(self.email_address, self.password)
        print("Connected to SMTP server.")

    def send_email(self, to_address, subject, body, html=False):
        """Send an email via Hotmail SMTP."""
        msg = MIMEMultipart("alternative")
        msg["From"] = self.email_address
        msg["To"] = to_address
        msg["Subject"] = subject

        content_type = "html" if html else "plain"
        msg.attach(MIMEText(body, content_type))

        self.smtp_conn.sendmail(self.email_address, to_address, msg.as_string())
        print(f"Email sent to {to_address}.")

    def disconnect_smtp(self):
        """Close the SMTP connection."""
        if self.smtp_conn:
            self.smtp_conn.quit()
            self.smtp_conn = None
            print("Disconnected from SMTP server.")


def _decode_header(value):
    """Decode an email header value."""
    if value is None:
        return ""
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return " ".join(result)


# -- Example usage --

if __name__ == "__main__":
    addr = input("Hotmail/Outlook email: ")
    pw = getpass.getpass("Password (or App Password): ")

    client = HotmailClient(addr, pw)

    # Read emails
    try:
        client.connect_imap()
        print("\n--- Recent Emails ---")
        for msg in client.fetch_recent_emails(count=3):
            print(f"From: {msg['from']}")
            print(f"Date: {msg['date']}")
            print(f"Subject: {msg['subject']}")
            print(f"Body: {msg['body'][:200]}...")
            print("-" * 40)
    finally:
        client.disconnect_imap()

    # Send email example (uncomment to use)
    # try:
    #     client.connect_smtp()
    #     client.send_email("recipient@example.com", "Test", "Hello from Python!")
    # finally:
    #     client.disconnect_smtp()
