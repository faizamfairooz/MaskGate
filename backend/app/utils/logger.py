import logging
from app.config.settings import settings


def setup_logger(name: str = "maskgate") -> logging.Logger:
    """Set up and configure a logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)

    # Add handler if not already present
    if not logger.handlers:
        logger.addHandler(console_handler)

    return logger


# Global logger instance
logger = setup_logger()
