"""
logger.py — Centralized logging configuration.

Usage in any module:
    from utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Pipeline started")
"""

import logging
import sys


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Create and return a configured logger instance.

    Args:
        name:  Typically __name__ of the calling module.
        level: Logging level (default INFO).

    Returns:
        A logging.Logger with console output and a consistent format.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if get_logger is called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # ── Console handler ──────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)-7s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Prevent log propagation to root logger (avoids duplicate messages)
    logger.propagate = False

    return logger
