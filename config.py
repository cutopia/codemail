"""
Configuration management for Codemail system.
Loads environment variables and provides configuration objects.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class EmailConfig:
    """Email server configuration."""
    
    def __init__(self):
        self.imap_host = os.getenv("IMAP_HOST", "imap.gmail.com")
        self.imap_port = int(os.getenv("IMAP_PORT", "993"))
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_address = os.getenv("EMAIL_ADDRESS")
        
        # Strip quotes from password if present
        password = os.getenv("EMAIL_PASSWORD")
        if password and len(password) >= 2:
            if (password.startswith('"') and password.endswith('"')) or \
               (password.startswith("'") and password.endswith("'")):
                password = password[1:-1]
        self.email_password = password
        
        # Codemail subject prefix
        self.codemail_prefix = os.getenv("CODEMAIL_PREFIX", "codemail:")
        
        # Email whitelist configuration
        # Format: comma-separated email addresses (e.g., "user1@example.com,user2@example.com")
        self.email_whitelist_senders = os.getenv("EMAIL_WHITELIST_SENDERS", "")
        self.email_whitelist_recipients = os.getenv("EMAIL_WHITELIST_RECIPIENTS", "")
        
    def validate(self):
        """Validate that required email configuration is present."""
        if not all([self.email_address, self.email_password]):
            raise ValueError("EMAIL_ADDRESS and EMAIL_PASSWORD must be set in environment variables")
    
    def validate_whitelist(self):
        """
        Validate whitelist configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # If no whitelist is configured, allow all (for backward compatibility)
        if not self.email_whitelist_senders and not self.email_whitelist_recipients:
            return True, None
        
        # Check sender whitelist format
        if self.email_whitelist_senders:
            senders = [s.strip() for s in self.email_whitelist_senders.split(',') if s.strip()]
            for sender in senders:
                if not self._is_valid_email(sender) and not sender.startswith('@'):
                    return False, f"Invalid email format in EMAIL_WHITELIST_SENDERS: {sender}"
        
        # Check recipient whitelist format
        if self.email_whitelist_recipients:
            recipients = [r.strip() for r in self.email_whitelist_recipients.split(',') if r.strip()]
            for recipient in recipients:
                if not self._is_valid_email(recipient) and not recipient.startswith('@'):
                    return False, f"Invalid email format in EMAIL_WHITELIST_RECIPIENTS: {recipient}"
        
        return True, None
    
    def _is_valid_email(self, email: str) -> bool:
        """Check if an email address has a valid format."""
        # Simple email regex pattern
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


class LLMConfig:
    """LLM endpoint configuration."""
    
    def __init__(self):
        self.endpoint = os.getenv("LLM_ENDPOINT", "http://127.0.0.1:1234/v1/models")
        self.api_key = os.getenv("LLM_API_KEY", "dummy_key")


class DatabaseConfig:
    """Database configuration."""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///tasks.db")


class RedisConfig:
    """Redis configuration for Celery queue."""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")


# Global configuration instances
email_config = EmailConfig()
llm_config = LLMConfig()
database_config = DatabaseConfig()
redis_config = RedisConfig()
