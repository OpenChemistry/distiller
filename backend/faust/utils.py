import re
from pathlib import Path

import aiohttp
import tenacity

from config import settings
from schemas import Scan, ScanCreate, ScanUpdate

pattern = re.compile(r"^log_scan([0-9]*)_.*\.data")


def extract_scan_id(path: str) -> int:
    filename = Path(path).name

    match = pattern.match(filename)
    if not match:
        raise ValueError("Unable to extract scan id.")

    return int(match.group(1))


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    ),
    wait=tenacity.wait_exponential(max=10),
    stop=tenacity.stop_after_attempt(10),
)
async def create_scan(session: aiohttp.ClientSession, event: ScanCreate) -> Scan:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    async with session.post(
        f"{settings.API_URL}/scans", headers=headers, data=event.json()
    ) as r:
        r.raise_for_status()
        json = await r.json()

        return Scan(**json)


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    ),
    wait=tenacity.wait_exponential(max=10),
    stop=tenacity.stop_after_attempt(10),
)
async def update_scan(session: aiohttp.ClientSession, event: ScanUpdate) -> dict:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    async with session.patch(
        f"{settings.API_URL}/scans/{event.id}", headers=headers, data=event.json()
    ) as r:
        r.raise_for_status()
        json = await r.json()

        return Scan(**json)


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    ),
    wait=tenacity.wait_exponential(max=10),
    stop=tenacity.stop_after_attempt(10),
)
async def get_scan(session: aiohttp.ClientSession, scan_id: int, state: str) -> dict:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    params = {"scan_id": scan_id, "state": state}

    async with session.patch(
        f"{settings.API_URL}/scans", headers=headers, params=params
    ) as r:
        r.raise_for_status()
        json = await r.json()

        return Scan(**json)
