import asyncio
import logging
import platform
import re
import signal
import sys
import tenacity
import aiohttp
from logging.handlers import RotatingFileHandler
from config import settings
import coloredlogs
from schemas import Microscope

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
        settings.LOG_FILE_PATH, maxBytes=104857600, backupCount=10 # 100MB
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    ) | tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ClientConnectionError
    ),
    wait=tenacity.wait_exponential(max=settings.MAX_WAIT),
    stop=tenacity.stop_after_attempt(settings.MAX_RETRIES),
)
async def get_microscope(session: aiohttp.ClientSession, name: str) -> Microscope:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    async with session.get(
        f"{settings.API_URL}/microscopes", headers=headers, params={"name": name}
    ) as r:
        r.raise_for_status()

        json = await r.json()

        if len(json) != 1:
            raise Exception("Unable to fetch microscopy")

        return Microscope(**json[0])

@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    ) | tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ClientConnectionError
    ),
    wait=tenacity.wait_exponential(max=settings.MAX_WAIT),
    stop=tenacity.stop_after_attempt(settings.MAX_RETRIES),
)
async def get_microscope_by_id(session: aiohttp.ClientSession, id: int) -> Microscope:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    async with session.get(
        f"{settings.API_URL}/microscopes/{id}", headers=headers
    ) as r:
        r.raise_for_status()

        json = await r.json()

        if json is None:
            raise Exception("Unable to fetch microscopy")

        return Microscope(**json)