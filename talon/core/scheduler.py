import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from typing import Any, Callable, Coroutine

class TalonScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._running = False

    def add_job(self, func: Callable[..., Coroutine[Any, Any, Any]], *args, **kwargs):
        self.scheduler.add_job(func, *args, **kwargs)

    def start(self):
        if not self._running:
            self.scheduler.start()
            self._running = True

    def shutdown(self):
        if self._running:
            self.scheduler.shutdown()
            self._running = False
