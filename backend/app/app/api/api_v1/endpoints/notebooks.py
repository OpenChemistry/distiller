import asyncio
from copy import deepcopy
from datetime import datetime, timedelta
from typing import List

from aiopath import AsyncPath
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, oauth2_password_bearer_or_api_key
from app.core.config import settings
from app.core.constants import DATE_DIR_FORMAT
from app.crud import microscope as microscope_crud
from app.crud import scan as scan_crud
from app.kafka.producer import send_notebook_event_to_kafka
from app.models import Scan
from app.schemas import (Notebook, NotebookCreate, NotebookCreateEvent,
                         NotebookSpecificationResponse, Scan)

router = APIRouter()


async def notebook_base_path(db: Session, scan: Scan):
    created_datetime = scan.created
    date_dir = created_datetime.astimezone().strftime(DATE_DIR_FORMAT)

    # 4D camera
    if scan.microscope_id == 1:
        notebook_path = AsyncPath(settings.NCEMHUB_PATH) / "counted" / date_dir
    else:
        microscope = microscope_crud.get_microscope(db, scan.microscope_id)
        if microscope is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan not found",
            )
        microscope_name = microscope.name.lower().replace(" ", "")
        notebook_path = (
            AsyncPath(settings.NCEMHUB_PATH)
            / "scans"
            / microscope_name
            / date_dir
            / str(scan.id)
        )

    return notebook_path


@router.post(
    "",
    response_model=Notebook,
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
async def create_notebook(notebook: NotebookCreate, db: Session = Depends(get_db)):
    scan = scan_crud.get_scan(db, notebook.scan_id)
    notebook_path = await notebook_base_path(db, scan)
    template_name = notebook.name.replace(".ipynb.j2", "")
    notebook_name = f"{template_name}_{scan.id}.ipynb"

    notebook_path = notebook_path / notebook_name

    # If we already have the notebook just the path
    if await notebook_path.exists():
        return Notebook(path=str(notebook_path))

    # Trigger the creation
    await send_notebook_event_to_kafka(
        NotebookCreateEvent(
            name=notebook.name, path=str(notebook_path), scan_id=scan.id
        )
    )

    start = datetime.utcnow()
    delta = timedelta(seconds=10)

    # Wait for the notebook to appear
    while datetime.utcnow() < start + delta:
        await asyncio.sleep(1)

        if await notebook_path.exists():
            break

    if await notebook_path.exists():
        return Notebook(path=str(notebook_path))
    else:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Notebook not generates within timeout",
        )


notebooks = None


@router.get(
    "",
    response_model=List[NotebookSpecificationResponse],
    dependencies=[Depends(oauth2_password_bearer_or_api_key)],
)
def read_notebooks(db: Session = Depends(get_db)):
    global notebooks
    if notebooks is None:
        notebooks = deepcopy(settings.NOTEBOOKS)
        # convert microscope names to ids
        for n in notebooks:
            if n.microscopes is None:
                continue

            microscopeIds = []
            for name in n.microscopes:
                [microscope] = microscope_crud.get_microscopes(db, name)
                microscopeIds.append(microscope.id)
            n.microscopes = microscopeIds

    return notebooks
