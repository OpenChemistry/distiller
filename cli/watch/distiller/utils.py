import asyncio
import logging
import platform
import re
import signal
import sys
from logging.handlers import RotatingFileHandler
from config import settings
import coloredlogs

# Setup logger
logger = logging.getLogger("watch")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = coloredlogs.ColoredFormatter(
    "%(asctime)s,%(msecs)03d - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
if settings.LOG_FILE_PATH is not None:
    file_handler = RotatingFileHandler(
        settings.LOG_FILE_PATH, maxBytes=102400, backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)