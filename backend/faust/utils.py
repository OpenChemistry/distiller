import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import tenacity
from aiopath import AsyncPath

from config import settings
from schemas import (Job, JobUpdate, Machine, Microscope, Scan, ScanCreate,
                     ScanUpdate)

logger = logging.getLogger("utils")
logger.setLevel(logging.INFO)

pattern = re.compile(r"^4dstem_rec_status_[0123]{1}_scan_([0-9]*)\.json")


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
    wait=tenacity.wait_exponential(max=settings.MAX_WAIT),
    stop=tenacity.stop_after_attempt(settings.MAX_RETRIES),
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
    wait=tenacity.wait_exponential(max=settings.MAX_WAIT),
    stop=tenacity.stop_after_attempt(settings.MAX_RETRIES),
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
    wait=tenacity.wait_exponential(max=settings.MAX_WAIT),
    stop=tenacity.stop_after_attempt(settings.MAX_RETRIES),
)
async def get_scans(
    session: aiohttp.ClientSession,
    scan_id: Optional[int] = None,
    state: Optional[str] = None,
    created: Optional[datetime] = None,
    sha: Optional[str] = None,
    uuid: Optional[str] = None,
    microscope_id: Optional[int] = None,
    limit: Optional[int] = None,
) -> List[Scan]:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    params: Dict[str, Any] = {}

    if scan_id is not None:
        params["scan_id"] = scan_id

    if state is not None:
        params["state"] = state

    if created is not None:
        params["created"] = created

    if sha is not None:
        params["sha"] = sha

    if uuid is not None:
        params["uuid"] = uuid

    if microscope_id is not None:
        params["microscope_id"] = microscope_id

    if limit is not None:
        params["limit"] = limit

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
    wait=tenacity.wait_exponential(max=settings.MAX_WAIT),
    stop=tenacity.stop_after_attempt(settings.MAX_RETRIES),
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
    wait=tenacity.wait_exponential(max=settings.MAX_WAIT),
    stop=tenacity.stop_after_attempt(settings.MAX_RETRIES),
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
    wait=tenacity.wait_exponential(max=settings.MAX_WAIT),
    stop=tenacity.stop_after_attempt(settings.MAX_RETRIES),
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
    wait=tenacity.wait_exponential(max=settings.MAX_WAIT),
    stop=tenacity.stop_after_attempt(settings.MAX_RETRIES),
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
    wait=tenacity.wait_exponential(max=settings.MAX_WAIT),
    stop=tenacity.stop_after_attempt(settings.MAX_RETRIES),
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
    wait=tenacity.wait_exponential(max=settings.MAX_WAIT),
    stop=tenacity.stop_after_attempt(settings.MAX_RETRIES),
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
    wait=tenacity.wait_exponential(max=settings.MAX_WAIT),
    stop=tenacity.stop_after_attempt(settings.MAX_RETRIES),
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
    )
    | tenacity.retry_if_exception_type(aiohttp.client_exceptions.ClientConnectionError),
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


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(
        aiohttp.client_exceptions.ServerConnectionError
    )
    | tenacity.retry_if_exception_type(aiohttp.client_exceptions.ClientConnectionError),
    wait=tenacity.wait_exponential(max=settings.MAX_WAIT),
    stop=tenacity.stop_after_attempt(settings.MAX_RETRIES),
)
async def get_notebooks(session: aiohttp.ClientSession, id: int) -> List[str]:
    headers = {
        settings.API_KEY_NAME: settings.API_KEY,
        "Content-Type": "application/json",
    }

    async with session.get(
        f"{settings.API_URL}/scans/{id}/notebooks", headers=headers
    ) as r:
        r.raise_for_status()

        json = await r.json()

        if json is None:
            raise Exception("Unable to fetch microscopy")

        return json


async def generate_ncemhub_scan_path(
    session: aiohttp.ClientSession, base_path: str, created_date: str, id: int
) -> AsyncPath:
    # ncemhub path are of the form <created date dir>/microscope/<id>
    # First get the microscope name to use for the directory
    scan = await get_scan(session, id)
    microscope = await get_microscope_by_id(session, scan.microscope_id)
    name = microscope.name.lower().replace(" ", "")

    date_dir = AsyncPath(created_date)

    return AsyncPath(base_path) / name / date_dir / str(id)
