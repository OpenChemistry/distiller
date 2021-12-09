import asyncio
from typing import Optional, Union

from watchdog.events import (DirCreatedEvent, DirDeletedEvent,
                             DirModifiedEvent, DirMovedEvent, FileClosedEvent,
                             FileCreatedEvent, FileDeletedEvent,
                             FileModifiedEvent, FileMovedEvent,
                             FileSystemEventHandler)


class AIOEventHandler(FileSystemEventHandler):
    def __init__(
        self, queue: asyncio.Queue, loop: asyncio.BaseEventLoop, *args, **kwargs
    ):
        self._loop = loop
        self._queue = queue
        super(*args, **kwargs)

    def on_created(self, event: Union[DirCreatedEvent, FileCreatedEvent]) -> None:
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)

    def on_deleted(self, event: Union[DirDeletedEvent, FileDeletedEvent]) -> None:
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)

    def on_modified(self, event: Union[DirModifiedEvent, FileModifiedEvent]) -> None:
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)

    def on_moved(self, event: Union[DirMovedEvent, FileMovedEvent]) -> None:
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)

    def on_closed(self, event: FileClosedEvent) -> None:
        self._loop.call_soon_threadsafe(self._queue.put_nowait, event)


class AIOEventIterator(object):
    def __init__(
        self, queue: asyncio.Queue, loop: Optional[asyncio.BaseEventLoop] = None
    ):
        self.queue = queue

    def __aiter__(self):
        return self

    async def __anext__(self):
        item = await self.queue.get()

        if item is None:
            raise StopAsyncIteration

        return item
