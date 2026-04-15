
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from config import settings

class EmailHandler:
    def __init__(self):
        self.imap_host = settings.IMAP_HOST
        self.imap_port = settings.IMAP_PORT
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.email_address = settings.EMAIL_ADDRESS
        self.email_password = settings.EMAIL_PASSWORD

    def connect_imap(self):
        mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
        mail.login(self.email_address, self.email_password)
        return mail

    def send_email(self, recipient, subject, body):
        msg = MIMEMultipart()
        msg['From'] = self.email_address
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.email_address, self.email_password)
            server.send_message(msg)

    def fetch_new_emails(self):
        mail = self.connect_imap()
        mail.select("inbox")
        
        # Search for unread emails with specific subject prefix
        status, messages = mail.search(None, '(UNSEEN SUBJECT "codemail:")')
        if status != 'OK' : 
            return []

        email_ids = messages[0].split()
        tasks = []

        for e_id in email_ids:
            res, msg_data = mail.fetch(e_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    sender = msg['From']
                    recipient = msg['To']
                    subject = msg['Subject']
                    
                    # Extract sender email from "Name <email@domain.com>"
                    sender_email = re.search(r'<(.*)>', sender).group(1) if '<' in sender else sender
                    
                    # Check Recipient Whitelist
                    recipients_list = [re.search(r'<(.*)>', r).group(1) if '<' in r else r for r in recipient.split(',')]
                    if not any(r.strip() in settings.EMAIL_WHITELIST_RECIPIENTS for r in recipients_list):
                        print(f"Ignored email sent to non-whitelisted recipient: {recipient}")
                        continue

                    # Check Sender Whitelist
                    if sender_email not in settings.EMAIL_WHITELIST_SENDERS:
                        print(f"Ignored email from non-whitelisted sender: {sender_email}")
                        continue

                    # Validate Subject Format: codemail:[<projectnamehere>]
                    match = re.search(r'codemail:\[(.*?)\]', subject, re.IGNORECASE)
                    if not match:
                        print(f"Invalid subject format: {subject}")
                        continue
                    
                    project_name = match.group(1)
                    body = self._get_email_body(msg)
                    
                    tasks.append({
                        'sender': sender_email,
                        'project': project_name,
                        'instructions': body,
                        'subject': subject
                    })
        
        mail.logout()
        return tasks

    def _get_email_body(self, msg):
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode()
        else:
            return msg.get_payload(decode=True).decode()
        return ""
