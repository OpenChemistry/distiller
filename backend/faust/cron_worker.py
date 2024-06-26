import logging
from datetime import datetime, timedelta

import pytz
from aiopath import AsyncPath

import faust
from config import settings

# Setup logger
logger = logging.getLogger("cron_worker")
logger.setLevel(logging.INFO)

app = faust.App("distiller-cron", broker=settings.KAFKA_URL)


@app.crontab("0 0 * * *", timezone=pytz.timezone("US/Pacific"))
async def haadf_reaper():
    logger.info("Reaping unclaimed HAADF images.")
    expiration = timedelta(hours=settings.HAADF_IMAGE_UPLOAD_DIR_EXPIRATION_HOURS)
    now = datetime.now().astimezone()
    format = settings.IMAGE_FORMAT

    async for f in AsyncPath(settings.IMAGE_UPLOAD_DIR).glob(f"*.{format}"):
        stat_info = await f.stat()
        created = datetime.fromtimestamp(stat_info.st_ctime).astimezone()

        if now - created > expiration:
            logger.info(f"Removing: {f}")
            await f.unlink()
