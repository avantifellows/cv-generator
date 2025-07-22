"""
Logging configuration for CV Generator application
"""
import logging
import sys
from typing import Optional
import os


def setup_logging(level: str = "INFO", format_string: Optional[str] = None) -> None:
    """
    Setup application logging
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # In AWS Lambda, only log to stdout
    if "AWS_LAMBDA_FUNCTION_NAME" in os.environ:
        handlers = [logging.StreamHandler(sys.stdout)]
    else:
        handlers = [
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log")
        ]
        
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=handlers
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)