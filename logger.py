"""
Logging configuration for Codemail system.
Provides consistent logging across all components.
"""

import logging
import os

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/codemail.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("codemail")
