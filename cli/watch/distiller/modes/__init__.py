from abc import ABC, abstractmethod

import aiohttp
from watchdog.events import FileSystemEvent

class ModeHandler(ABC):
    def __init__(self, microscope_id: int,  host: str, session: aiohttp.ClientSession):
        self.microscope_id = microscope_id
        self.host = host
        self.session = session

    @abstractmethod
    async def on_event(self, event: FileSystemEvent):
        pass

    async def sync(self):
        pass