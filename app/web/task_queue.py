from asyncio.log import logger

from celery import Celery
from sqlalchemy import or_
from sqlalchemy.orm import Session

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
        transcribe.delay(job.id)

    def rehydrate(self, session: Session):
        # TODO: we could use `acks_late` to handle this scenario within celery itself.
        # the reason this does not work well in our case is that `visibility_timeout`
        # needs to be very high since whisper workers can be long running.
        # doing this app-side bears the risk of poison pilling the worker though,
        # implement a workaround with an acceptable trade-off. (=> retry only once?)
        jobs = (
            session.query(models.Job)
            .filter(
                or_(
                    models.Job.status == models.JobStatus.processing,
                    models.Job.status == models.JobStatus.create,
                )
            )
            .order_by(models.Job.created_at)
        ).all()

        logger.info(f"Requeueing {len(jobs)} jobs.")

        for job in jobs:
            self.queue_task(job)
