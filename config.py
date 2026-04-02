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
        
    def validate(self):
        """Validate that required email configuration is present."""
        if not all([self.email_address, self.email_password]):
            raise ValueError("EMAIL_ADDRESS and EMAIL_PASSWORD must be set in environment variables")


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
