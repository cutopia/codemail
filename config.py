
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.IMAP_HOST = os.getenv("IMAP_HOST")
        self.IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
        self.SMTP_HOST = os.getenv("SMTP_HOST")
        self.SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
        self.EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
        self.EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
        self.LLM_ENDPOINT = os.getenv("LLM_ENDPOINT")
        self.LLM_API_KEY = os.getenv("LLM_API_KEY", "dummy")
        self.DATABASE_URL = os.getenv("DATABASE_URL")
        self.REDIS_URL = os.getenv("REDIS_URL")
        
        # Parse comma-separated lists
        senders_str = os.getenv("EMAIL_WHITELIST_SENDERS", "")
        recipients_str = os.getenv("EMAIL_WHITELIST_RECIPIENTS", "")
        self.EMAIL_WHITELIST_SENDERS = [s.strip() for s in senders_str.split(",") if s.strip()]
        self.EMAIL_WHITELIST_RECIPIENTS = [r.strip() for r in recipients_str.split(",") if r.strip()]
        
        self.LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 4096))
        self.LLM_DEBUG_LOGGING = os.getenv("LLM_DEBUG_LOGGING", "false").lower() == "true"
        self.PROJECTS_BASE_DIR = os.getenv("PROJECTS_BASE_DIR", "~/projects")

settings = Settings()
