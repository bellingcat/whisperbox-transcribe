from asyncio.log import logger
from typing import Any, Optional
from uuid import UUID

from celery import Task
from sqlalchemy.orm import Session

import app.shared.db.models as models
import app.shared.db.schemas as schemas
from app.shared.celery import get_celery_binding
from app.shared.db.base import SessionLocal
from app.shared.settings import settings
from app.worker.strategies.local import LocalStrategy

celery = get_celery_binding()


class TranscribeTask(Task):
    abstract = True

    def __init__(self) -> None:
        super().__init__()
        # currently only `LocalStrategy` is implemented.
        self.strategy: Optional[LocalStrategy] = None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        # load model into memory once when the first task is processed.
        if not self.strategy:
            self.strategy = LocalStrategy()
        return self.run(*args, **kwargs)


def select_strategy(task: Task, job: schemas.Job) -> Any:
    if job.type == schemas.JobType.transcript:
        return task.strategy.transcribe
    elif job.type == schemas.JobType.translation:
        return task.strategy.translate
    else:
        return task.strategy.detect_language


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

        job = db.query(models.Job).filter(models.Job.id == job_id).one()

        if (
            job.status == schemas.JobStatus.error
            or job.status == schemas.JobStatus.success
        ):
            logger.warn(
                "[{job.id}]: Received job that has already been processed, abort."
            )
            return

        logger.info(f"[{job.id}]: worker received task.")

        job.meta = {"task_id": self.request.id}
        job.status = schemas.JobStatus.processing
        db.commit()
        logger.info(f"[{job.id}]: set task to status processing.")

        job_record = schemas.Job.from_orm(job)

        strategy = select_strategy(self, job_record)
        result = strategy(
            url=job_record.url, job_id=job_record.id, config=job_record.config
        )

        logger.info(f"[{job.id}]: successfully processed audio.")

        artifact = models.Artifact(
            job_id=str(job.id), data=result, type=schemas.ArtifactType.raw_transcript
        )

        db.add(artifact)
        db.commit()
        logger.info(f"[{job.id}]: successfully stored artifact.")

        job.status = schemas.JobStatus.success
        db.commit()

        logger.info(f"[{job.id}]: set task to status success.")
    except Exception as e:
        if job and db:
            job.meta = {**job.meta, "error": str(e)}  # type: ignore
            job.status = schemas.JobStatus.error
            db.commit()
        raise (e)
    finally:
        self.strategy.cleanup(job_id=job_id)
        db.close()
