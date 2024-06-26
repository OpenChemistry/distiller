import logging
from pathlib import Path

import aiohttp
import jinja2
from aiopath import AsyncPath

import faust
from config import settings
from constants import DATE_DIR_FORMAT, TOPIC_NOTEBOOK_EVENTS
from schemas import Scan
from utils import get_scan

# Setup logger
logger = logging.getLogger("notebook_worker")
logger.setLevel(logging.INFO)

app = faust.App(
    "distiller-notebook",
    store="rocksdb://",
    broker=settings.KAFKA_URL,
    topic_partitions=1,
)


class NotebookCreateEvent(faust.Record):
    scan_id: int
    name: str
    path: str


notebook_create_events_topic = app.topic(
    TOPIC_NOTEBOOK_EVENTS, value_type=NotebookCreateEvent
)


async def render_notebook(
    scan: Scan, notebook_name: str, scan_created_date: str
) -> str:
    template_loader = jinja2.FileSystemLoader(
        searchpath=Path(__file__).parent / "templates"
    )
    template_env = jinja2.Environment(loader=template_loader, enable_async=True)
    template = template_env.get_template(f"{notebook_name}.ipynb.j2")

    return await template.render_async(
        settings=settings, scan=scan, scan_created_date=scan_created_date
    )


async def generate_notebook(scan: Scan, notebook_name: str, notebook_path: AsyncPath):
    await notebook_path.parent.mkdir(parents=True, exist_ok=True)
    scan_created_date = scan.created.astimezone().strftime(DATE_DIR_FORMAT)
    notebook_contents = await render_notebook(scan, notebook_name, scan_created_date)
    async with notebook_path.open("w") as fp:
        await fp.write(notebook_contents)

    return notebook_path


async def process_notebook_create_event(
    session: aiohttp.ClientSession, event: NotebookCreateEvent
):
    scan = await get_scan(session, event.scan_id)
    notebook_path = AsyncPath(event.path)

    if not await notebook_path.exists():
        await generate_notebook(scan, event.name, notebook_path)


@app.agent(notebook_create_events_topic)
async def watch_for_notebook_create_events(notebook_create_events):
    async with aiohttp.ClientSession() as session:
        async for event in notebook_create_events:
            await process_notebook_create_event(session, event)
