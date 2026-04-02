"""
Email monitoring module for Codemail system.
Monitors email inbox for new messages and processes them.
"""

import imaplib
import email
from email.header import decode_header
import time
import logging
from config import email_config

logger = logging.getLogger("codemail.email_monitor")


class EmailMonitor:
    """IMAP email monitor that checks for new emails."""
    
    def __init__(self):
        self.imap_host = email_config.imap_host
        self.imap_port = email_config.imap_port
        self.email_address = email_config.email_address
        self.email_password = email_config.email_password
        
    def connect(self):
        """Connect to IMAP server."""
        try:
            # Connect to the IMAP server
            imap = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            
            # Login to the account
            imap.login(self.email_address, self.email_password)
            
            return imap
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {e}")
            raise
    
    def select_inbox(self, imap_conn):
        """Select the inbox folder."""
        try:
            status, _ = imap_conn.select("INBOX")
            if status != "OK":
                raise Exception("Failed to select INBOX")
            return True
        except Exception as e:
            logger.error(f"Failed to select INBOX: {e}")
            raise
    
    def search_unread_emails(self, imap_conn):
        """Search for unread emails."""
        try:
            # Search for unread messages
            status, data = imap_conn.search(None, 'UNSEEN')
            
            if status != "OK":
                logger.error("Failed to search for unread emails")
                return []
            
            # Get email IDs
            email_ids = data[0].split()
            return email_ids
            
        except Exception as e:
            logger.error(f"Error searching for unread emails: {e}")
            return []
    
    def fetch_email(self, imap_conn, email_id):
        """Fetch a specific email by ID."""
        try:
            # Fetch the email body (RFC822)
            status, msg_data = imap_conn.fetch(email_id, '(RFC822)')
            
            if status != "OK":
                logger.error(f"Failed to fetch email {email_id}")
                return None
            
            # Parse the email
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            return msg
            
        except Exception as e:
            logger.error(f"Error fetching email {email_id}: {e}")
            return None
    
    def mark_as_seen(self, imap_conn, email_id):
        """Mark an email as seen (read)."""
        try:
            # Add the \Seen flag
            status, _ = imap_conn.store(email_id, '+FLAGS', '\\Seen')
            
            if status != "OK":
                logger.error(f"Failed to mark email {email_id} as seen")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking email {email_id} as seen: {e}")
            return False
    
    def extract_email_content(self, msg):
        """Extract subject and body from email message."""
        try:
            # Decode subject
            subject, encoding = decode_header(msg.get("Subject", ""))[0]
            if isinstance(subject, bytes):
                if encoding:
                    subject = subject.decode(encoding)
                else:
                    subject = subject.decode('utf-8')
            
            # Get sender
            from_ = msg.get("From", "")
            
            # Extract body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    # Skip attachments
                    if "attachment" in content_disposition:
                        continue
                    
                    if content_type == "text/plain":
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            body = part.get_payload(decode=True).decode(charset)
                            break  # Get first text/plain part
                        except Exception as e:
                            logger.warning(f"Error decoding email body: {e}")
            else:
                charset = msg.get_content_charset() or 'utf-8'
                try:
                    body = msg.get_payload(decode=True).decode(charset)
                except Exception as e:
                    logger.warning(f"Error decoding email body: {e}")
            
            return {
                "from": from_,
                "subject": subject,
                "body": body.strip()
            }
            
        except Exception as e:
            logger.error(f"Error extracting email content: {e}")
            return None
    
    def monitor_loop(self, callback, poll_interval=60):
        """
        Monitor loop that continuously checks for new emails.
        
        Args:
            callback: Function to call with email data when new email found
            poll_interval: Seconds between checks (default 60)
        """
        logger.info(f"Starting email monitor for {self.email_address}")
        
        while True:
            try:
                # Connect to IMAP server
                imap = self.connect()
                
                # Select inbox
                self.select_inbox(imap)
                
                # Search for unread emails
                email_ids = self.search_unread_emails(imap)
                
                if email_ids:
                    logger.info(f"Found {len(email_ids)} unread emails")
                    
                    for email_id in email_ids:
                        # Fetch and process email
                        msg = self.fetch_email(imap, email_id)
                        
                        if msg:
                            email_data = self.extract_email_content(msg)
                            
                            if email_data:
                                logger.info(f"Processing email from {email_data['from']}")
                                
                                # Call callback with email data
                                callback(email_data)
                                
                                # Mark as seen after processing
                                self.mark_as_seen(imap, email_id)
                
                # Close connection and wait
                imap.close()
                imap.logout()
                
                logger.info(f"Waiting {poll_interval} seconds for next check...")
                time.sleep(poll_interval)
                
            except KeyboardInterrupt:
                logger.info("Email monitor stopped by user")
                break
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(poll_interval)  # Wait before retrying


def create_email_monitor():
    """Factory function to create email monitor with validation."""
    try:
        email_config.validate()
        return EmailMonitor()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
