from asyncio.log import logger
from typing import Any, Optional
from uuid import UUID

from celery import Task
from sqlalchemy.orm import Session

import app.shared.db.models as models
import app.shared.db.schemas as schemas
from app.shared.celery import get_celery_binding
from app.shared.db.base import SessionLocal
from app.worker.strategies.local import LocalStrategy

celery = get_celery_binding()


class TranscribeTask(Task):
    abstract = True

    def __init__(self) -> None:
        super().__init__()
        # currently only `LocalStrategy` is implemented.
        # TODO: implement remote processing strategy.
        self.strategy: Optional[LocalStrategy] = None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        # load model into memory once when the first task is processed.
        if not self.strategy:
            self.strategy = LocalStrategy()
        return self.run(*args, **kwargs)


@celery.task(base=TranscribeTask, bind=True, soft_time_limit=2 * 60 * 60)
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

        job.meta = {"task_id": self.request.id}
        job.status = schemas.JobStatus.processing
        db.commit()

        logger.info(f"[{job.id}]: set task to status processing.")

        job_record = schemas.Job.from_orm(job)

        # process selected task.
        if job.type == schemas.JobType.transcript:
            result = self.strategy.transcribe(
                url=job_record.url, job_id=job_record.id, config=job_record.config
            )
        elif job.type == schemas.JobType.translation:
            result = self.strategy.translate(
                url=job_record.url, job_id=job_record.id, config=job_record.config
            )
        else:
            result = self.strategy.detect_language(
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
        db.close()
