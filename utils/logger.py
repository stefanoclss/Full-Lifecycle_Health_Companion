import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name: str):
    """
    Sets up a logger with a rotating file handler.
    """
    # Create logs directory if it doesn't exist
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    LOG_FILE = os.path.join(LOGS_DIR, "app.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # prevent adding multiple handlers if setup is called multiple times
    if not logger.handlers:
        # File Handler (Rotating)
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=50*1024*1024, backupCount=5, encoding="utf-8"
        )
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console Handler (Optional, for dev visibility)
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            "%(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger

# Default logger instance
logger = setup_logger("ArcVault")
