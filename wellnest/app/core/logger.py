import sys
from loguru import logger


def configure_logging():
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    )


def get_logger(name: str):
    return logger.bind(name=name)