import re
from datetime import datetime
from pathlib import Path
from typing import Union

import aiohttp
import tenacity

from config import settings
from schemas import Job, JobUpdate, Scan, ScanCreate, ScanUpdate

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
async def get_scans(
    session: aiohttp.ClientSession,
    scan_id: int,
    state: str = None,
    created: datetime = None,
) -> Union[Scan, None]:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    params = {"scan_id": scan_id}

    if state is not None:
        params["state"] = state

    if created is not None:
        params["created"] = created

    async with session.get(
        f"{settings.API_URL}/scans", headers=headers, params=params
    ) as r:
        r.raise_for_status()
        json = await r.json()

        return [Scan(**x) for x in json]


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    ),
    wait=tenacity.wait_exponential(max=10),
    stop=tenacity.stop_after_attempt(10),
)
async def update_job(session: aiohttp.ClientSession, event: JobUpdate) -> dict:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    async with session.patch(
        f"{settings.API_URL}/jobs/{event.id}", headers=headers, data=event.json()
    ) as r:
        r.raise_for_status()
        json = await r.json()

        return Job(**json)


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    ),
    wait=tenacity.wait_exponential(max=10),
    stop=tenacity.stop_after_attempt(10),
)
async def get_jobs(session: aiohttp.ClientSession, slurm_id: int) -> Union[Scan, None]:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    params = {"slurm_id": slurm_id}

    async with session.get(
        f"{settings.API_URL}/jobs", headers=headers, params=params
    ) as r:
        r.raise_for_status()
        json = await r.json()

        return [Job(**x) for x in json]


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    ),
    wait=tenacity.wait_exponential(max=10),
    stop=tenacity.stop_after_attempt(10),
)
async def get_job(session: aiohttp.ClientSession, id: int) -> Union[Scan, None]:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    async with session.get(f"{settings.API_URL}/jobs/{id}", headers=headers) as r:
        r.raise_for_status()
        json = await r.json()

        return Job(**json)
