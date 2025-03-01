"""
Centralized logging configuration using Loguru.

This module initializes a Loguru logger that can be imported and used throughout the application.
"""

import os
import sys
from pathlib import Path

from loguru import logger

# Constants for log directory and default log level
DEFAULT_LOG_LEVEL = "INFO"
APP_NAME = "wildfire_simulation"

# Get log directory
LOG_DIR = str(Path.home() / f".{APP_NAME}" / "logs")

# Ensure log directory exists
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)


def get_logger(module_name: str = None):
    """
    Get a logger instance with the module name.

    Args:
        module_name: Optional module name. If not provided, uses the caller's module name.

    Returns:
        A configured logger instance
    """
    # If module_name not provided, use the caller's module name
    if module_name is None:
        import inspect
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        module_name = module.__name__ if module else "unnamed"

    return logger.bind(name=module_name)


# Export logger for direct import
log = logger
