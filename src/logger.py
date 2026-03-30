import logging
import sys
from colorlog import ColoredFormatter

def setup_logger(name="GenoshideBot", log_level=logging.INFO):
    """
    Sets up a professional logger with colored console output and file logging.
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Avoid duplicate logs if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formatter for console output (Includes thread name for multi-account tracking)
    console_formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s | %(levelname)-8s | [%(threadName)s] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        }
    )

    # Formatter for file output (no colors)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)-8s | [%(threadName)s] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler("genoshide_bot.log", encoding="utf-8")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger

# Global logger instance
logger = setup_logger()
