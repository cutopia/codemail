"""
Email whitelist module for Codemail system.
Manages email address whitelisting for incoming and outgoing emails.
"""

import os
import logging
from email.utils import parseaddr
from typing import List, Set, Optional

logger = logging.getLogger("codemail.whitelist")


class EmailWhitelist:
    """Manages email address whitelist for incoming and outgoing emails."""
    
    def __init__(self):
        # Load environment variables from .env file if it exists
        from dotenv import load_dotenv
        load_dotenv()
        
        # Get whitelisted senders from environment variable
        sender_list = os.getenv("EMAIL_WHITELIST_SENDERS", "")
        self.allowed_senders: Set[str] = set()
        
        for email in sender_list.split(','):
            email = email.strip().strip('"').strip("'")  # Remove surrounding quotes
            if email:
                # Normalize to lowercase
                self.allowed_senders.add(email.lower())
        
        # Get whitelisted recipients from environment variable
        recipient_list = os.getenv("EMAIL_WHITELIST_RECIPIENTS", "")
        self.allowed_recipients: Set[str] = set()
        
        for email in recipient_list.split(','):
            email = email.strip().strip('"').strip("'")  # Remove surrounding quotes
            if email:
                # Normalize to lowercase
                self.allowed_recipients.add(email.lower())
        
        logger.info(f"Whitelist initialized with {len(self.allowed_senders)} allowed senders and {len(self.allowed_recipients)} allowed recipients")
    
    def is_sender_whitelisted(self, sender: str) -> bool:
        """
        Check if a sender email address is whitelisted.
        
        Args:
            sender: Email address to check
            
        Returns:
            True if whitelisted, False otherwise
        """
        # If no whitelist is configured (empty set), allow all for backward compatibility
        if not self.allowed_senders:
            return True
        
        if not sender:
            return False
        
        # Normalize sender to lowercase for comparison
        sender_normalized = sender.lower().strip()
        
        # Direct match
        if sender_normalized in self.allowed_senders:
            return True
        
        # Check if any whitelist entry is a domain (e.g., @example.com)
        for allowed in self.allowed_senders:
            if allowed.startswith('@') and sender_normalized.endswith(allowed):
                return True
        
        return False
    
    def is_recipient_whitelisted(self, recipient: str) -> bool:
        """
        Check if a recipient email address is whitelisted.
        
        Args:
            recipient: Email address to check
            
        Returns:
            True if whitelisted, False otherwise
        """
        # If no whitelist is configured (empty set), allow all for backward compatibility
        if not self.allowed_recipients:
            return True
        
        if not recipient:
            return False
        
        # Normalize recipient to lowercase for comparison
        recipient_normalized = recipient.lower().strip()
        
        # Direct match
        if recipient_normalized in self.allowed_recipients:
            return True
        
        # Check if any whitelist entry is a domain (e.g., @example.com)
        for allowed in self.allowed_recipients:
            if allowed.startswith('@') and recipient_normalized.endswith(allowed):
                return True
        
        return False
    
    def get_whitelisted_senders(self) -> List[str]:
        """Return list of whitelisted sender addresses."""
        return sorted(list(self.allowed_senders))
    
    def get_whitelisted_recipients(self) -> List[str]:
        """Return list of whitelisted recipient addresses."""
        return sorted(list(self.allowed_recipients))
    
    def _extract_email_address(self, from_field: str) -> str:
        """Extract email address from From field (handles 'Name <email>' format).
        
        Uses Python's built-in parseaddr which handles RFC-compliant email formats
        more reliably than regex patterns.
        """
        # Use email.utils.parseaddr to extract name and email address
        name, addr = parseaddr(from_field)
        
        # Return the email address (empty string if no valid email found)
        return addr.strip() if addr else from_field.strip()


def create_email_whitelist():
    """Factory function to create email whitelist with validation."""
    try:
        return EmailWhitelist()
    except Exception as e:
        logger.error(f"Error creating email whitelist: {e}")
        raise


# Global whitelist instance
email_whitelist = None


def get_email_whitelist() -> Optional[EmailWhitelist]:
    """Get or create the global whitelist instance."""
    global email_whitelist
    
    if email_whitelist is None:
        try:
            email_whitelist = EmailWhitelist()
        except Exception as e:
            logger.error(f"Failed to initialize email whitelist: {e}")
    
    return email_whitelist
