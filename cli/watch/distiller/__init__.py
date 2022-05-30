import asyncio
import logging
import platform
import re
import signal
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import List

import aiohttp
import coloredlogs
import tenacity
from aiopath import AsyncPath
from pathlib import Path
from aiowatchdog import AIOEventHandler, AIOEventIterator
from cachetools import TTLCache
from config import settings
from constants import LOG_FILE_GLOB
from schemas import File, WatchMode
from schemas import FileSystemEvent as FileSystemEventModel
from schemas import SyncEvent
from watchdog.events import (EVENT_TYPE_CLOSED, EVENT_TYPE_MODIFIED, EVENT_TYPE_CREATED,
                             EVENT_TYPE_MOVED, FileSystemEvent)
from watchdog.observers.polling import PollingObserver as Observer
from modes import scan_4d_files, scan_4d_haadf_files, scan_files