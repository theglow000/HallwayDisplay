"""
Logging utility for the Hallway Display system.
"""

import logging
import os
import sys
from datetime import datetime

# Define log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configure the logger
def setup_logger(name, level=logging.INFO):
    """Set up and return a logger with the given name and level.
    
    Args:
        name: The name of the logger.
        level: The logging level (default: INFO).
        
    Returns:
        A configured logger instance.
    """
    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create handlers
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # File handler (daily log file)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(LOG_DIR, f"{today}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    
    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to the logger
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger
