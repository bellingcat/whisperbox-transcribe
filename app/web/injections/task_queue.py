from functools import lru_cache

from fastapi import Depends

from app.shared.settings import Settings
from app.web.injections.settings import get_settings
from app.web.task_queue import TaskQueue


@lru_cache
def task_queue(broker_url: str):
    return TaskQueue(broker_url)


def get_task_queue(settings: Settings = Depends(get_settings)):
    return task_queue(settings.BROKER_URL)
