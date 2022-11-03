import re
from datetime import datetime
from pathlib import Path
from typing import List, Union, Optional, Dict, Any
import logging

import aiohttp
import tenacity

from config import settings
from schemas import (Job, JobUpdate, Machine, Microscope, Scan, ScanCreate,
                     ScanUpdate)

logger = logging.getLogger("utils")
logger.setLevel(logging.INFO)

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
async def update_scan(session: aiohttp.ClientSession, event: ScanUpdate) -> Scan:
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
    state: Optional[str] = None,
    created: Optional[datetime] = None,
    sha: Optional[str] = None,
    uuid: Optional[str] = None,
) -> List[Scan]:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    params: Dict[str, Any] = {"scan_id": scan_id}

    if state is not None:
        params["state"] = state

    if created is not None:
        params["created"] = created

    if sha is not None:
        params["sha"] = sha

    if uuid is not None:
        params["uuid"] = uuid

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
async def get_scan(session: aiohttp.ClientSession, id: int) -> Scan:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    async with session.get(f"{settings.API_URL}/scans/{id}", headers=headers) as r:
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
async def update_job(session: aiohttp.ClientSession, event: JobUpdate) -> Job:
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
async def get_jobs(session: aiohttp.ClientSession, slurm_id: int) -> List[Job]:
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
async def get_job(session: aiohttp.ClientSession, id: int) -> Job:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    async with session.get(f"{settings.API_URL}/jobs/{id}", headers=headers) as r:
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
async def delete_locations(session: aiohttp.ClientSession, id: int, host: str) -> None:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    params = {"host": host}

    try:
        async with session.delete(
            f"{settings.API_URL}/scans/{id}/locations", headers=headers, params=params
        ) as r:
            r.raise_for_status()
    except aiohttp.client_exceptions.ClientResponseError as ex:
        # Ignore 404, the scan may have been deleted
        if ex.status != 404:
            logger.exception("Exception deleting locations")


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    ),
    wait=tenacity.wait_exponential(max=10),
    stop=tenacity.stop_after_attempt(10),
)
async def get_machines(session: aiohttp.ClientSession) -> List[str]:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    async with session.get(f"{settings.API_URL}/machines", headers=headers) as r:
        r.raise_for_status()
        json = await r.json()

        # We only want the names
        return [m["name"] for m in json]


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    ),
    wait=tenacity.wait_exponential(max=10),
    stop=tenacity.stop_after_attempt(10),
)
async def get_machine(session: aiohttp.ClientSession, name: str) -> Machine:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    async with session.get(f"{settings.API_URL}/machines/{name}", headers=headers) as r:
        r.raise_for_status()
        json = await r.json()

        return Machine(**json)


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    )
    | tenacity.retry_if_exception_type(aiohttp.client_exceptions.ClientConnectionError),
    wait=tenacity.wait_exponential(max=10),
    stop=tenacity.stop_after_attempt(10),
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
