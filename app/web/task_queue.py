from celery import Celery

import app.shared.db.models as models
from app.shared.celery import get_celery_binding


class TaskQueue:
    celery: Celery

    def __init__(self) -> None:
        self.celery = get_celery_binding()

    def queue_task(self, job: models.Job):
        """
        Queues an async transcription job. We use a celery signature here to
        allow for full separation of worker processes and dependencies.
        """
        transcribe = self.celery.signature("app.worker.main.transcribe")
        # TODO: catch delivery errors?
        transcribe.delay(job.id)
