from asyncio.log import logger
from uuid import UUID

from celery import Task
from sqlalchemy.orm import Session

import app.shared.db.models as models
import app.shared.db.schemas as schemas
from app.shared.celery import get_celery_binding
from app.shared.db.base import SessionLocal
from app.worker.strategies.local import LocalStrategy

celery = get_celery_binding()


@celery.task(bind=True, soft_time_limit=2 * 60 * 60)  # TODO: make configurable
def transcribe(self: Task, job_id: UUID) -> None:
    try:
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

        # pick a transcription strategy.
        # currently only `local` is supported.
        job_record = schemas.Job.from_orm(job)
        strategy = LocalStrategy(
            db=db, job_id=job.id, url=job_record.url, config=job_record.config
        )

        # process selected task.
        # currently only `transcribe` is supported.
        if job.type == schemas.JobType.transcript:
            result = strategy.transcribe()
            logger.info(f"[{job.id}]: successfully transcribed audio.")
        elif job.type == schemas.JobType.translation:
            result = strategy.translate()
            logger.info(f"[{job.id}]: successfully translated audio.")
        else:
            result = strategy.detect_language()

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
            job.meta = {**job.meta.__dict__, "error": str(e)}
            job.status = schemas.JobStatus.error
            db.commit()
            raise (e)
    finally:
        db.close()
