import logging
from datetime import datetime, timedelta

import pytz
from aiopath import AsyncPath

import faust
from config import settings

# Setup logger
logger = logging.getLogger("cron_worker")
logger.setLevel(logging.INFO)

app = faust.App("still")


@app.crontab("0 0 * * *", timezone=pytz.timezone("US/Pacific"))
async def haadf_reaper():
    logger.info("Reaping unclaimed HAADF images.")
    expiration = timedelta(hours=settings.HAADF_IMAGE_UPLOAD_DIR_EXPIRATION_HOURS)
    now = datetime.now()
    async for f in AsyncPath(settings.HAADF_IMAGE_UPLOAD_DIR).glob("*.png"):
        stat_info = await f.stat()
        created = datetime.fromtimestamp(stat_info.st_ctime)

        if now - created > expiration:
            logger.info(f"Removing: {f}")
            await f.remove()
