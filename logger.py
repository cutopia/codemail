"""
Logging configuration for Codemail system.
Provides consistent logging across all components.
"""

import logging
import os

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Get log level from environment variable, default to INFO
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
level_map = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}
log_level = level_map.get(log_level, logging.INFO)

# Configure root logger
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/codemail.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("codemail")
