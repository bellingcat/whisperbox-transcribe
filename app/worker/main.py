from asyncio.log import logger
from typing import Any
from uuid import UUID

from celery import Task
from sqlalchemy.orm import Session

import app.shared.db.models as models
from app.shared.celery import get_celery_binding
from app.shared.db.base import SessionLocal
from app.shared.settings import settings
from app.worker.strategies.local import LocalStrategy

celery = get_celery_binding()


class TranscribeTask(Task):
    """
    Decorate the transcribe task with an instance of the transcription strategy.
    This is important for the local strategy, where loading the model is expensive.
    """

    abstract = True

    def __init__(self) -> None:
        super().__init__()
        # currently only `LocalStrategy` is implemented.
        self.strategy: LocalStrategy | None = None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        # load model into memory once when the first task is processed.
        if not self.strategy:
            self.strategy = LocalStrategy()
        return self.run(*args, **kwargs)


@celery.task(
    base=TranscribeTask,
    bind=True,
    soft_time_limit=settings.TASK_SOFT_TIME_LIMIT,
    time_limit=settings.TASK_HARD_TIME_LIMIT,
)
def transcribe(self: Task, job_id: UUID) -> None:
    try:
        # runs in a separate thread => requires sqlite's WAL mode to be enabled.
        db: Session = SessionLocal()

        # check if passed job should be processed.

        job = db.query(models.Job).filter(models.Job.id == job_id).one_or_none()

        if job is None:
            logger.warn("[{job.id}]: Received unknown job, abort.")
            return

        if job.status in [models.JobStatus.error, models.JobStatus.success]:
            logger.warn("[{job.id}]: job has already been processed, abort.")
            return

        logger.debug(f"[{job.id}]: start processing {job.type} job.")

        # unit of work: set task status to processing.

        job.meta = {"task_id": self.request.id}
        job.status = models.JobStatus.processing
        db.commit()

        logger.debug(f"[{job.id}]: finished setting task to {job.status}.")

        # unit of work: process job with whisper.
        result_type, result = self.strategy.process(job)
        logger.debug(f"[{job.id}]: successfully processed audio.")

        artifact = models.Artifact(job_id=str(job.id), data=result, type=result_type)
        db.add(artifact)

        job.status = models.JobStatus.success
        db.commit()

        logger.debug(f"[{job.id}]: successfully stored artifact.")

    except Exception as e:
        if job and db:
            if db.in_transaction():
                db.rollback()
            job.meta = {**job.meta, "error": str(e)}  # type: ignore
            job.status = models.JobStatus.error
            db.commit()
        raise
    finally:
        self.strategy.cleanup(job_id)
        db.close()
