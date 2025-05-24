import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

# Global store for logs to be displayed in UI for current command
current_task_logs = []

def setup_logger(name, log_file=None, level=logging.INFO):
    """Set up and return a logger with console and file handlers."""
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers = []  # Clear existing handlers to avoid duplicates

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create console handler and add to logger
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # If log file is specified, create file handler and add to logger
    if log_file:
        # Ensure directory exists
        log_dir = Path(log_file).parent
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# Main application logger
logger = setup_logger('browser_agent')

def log_step(message):
    """Log a step in the process and add to the current task logs."""
    logger.info(message)
    current_task_logs.append({"type": "info", "message": message})

def log_error(message):
    """Log an error and add to the current task logs."""
    logger.error(message)
    current_task_logs.append({"type": "error", "message": message})

def log_browser(message, url=None):
    """Log a browser action and add to the current task logs."""
    logger.info(f"[BROWSER] {message}")
    if url:
        current_task_logs.append({"type": "browser", "message": message, "url": url})
    else:
        current_task_logs.append({"type": "browser", "message": message})

def log_ai(message):
    """Log an AI action and add to the current task logs."""
    logger.info(f"[AI] {message}")
    current_task_logs.append({"type": "ai", "message": message})

def get_task_logs():
    """Return the current task logs."""
    return current_task_logs

def clear_task_logs():
    """Clear the current task logs."""
    global current_task_logs
    current_task_logs = []
