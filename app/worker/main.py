from asyncio.log import logger
from uuid import UUID

from sqlalchemy.orm import Session

import app.shared.db.dtos as dtos
import app.shared.db.models as models
from app.shared.celery import get_celery_binding
from app.shared.db.base import SessionLocal
from app.worker.strategies.local import LocalStrategy

celery = get_celery_binding()


def update_job_status(db: Session, job: models.Job, status: dtos.JobStatus) -> None:
    job.status = status
    db.commit()


@celery.task()
def transcribe(job_id: UUID) -> None:
    try:
        db: Session = SessionLocal()
        job = db.query(models.Job).filter(models.Job.id == job_id).one()

        update_job_status(db, job, dtos.JobStatus.processing)

        # pick a transcription strategy.
        # currently only `local` is supported.
        job_record = dtos.Job.from_orm(job)
        strategy = LocalStrategy(
            db=db, job_id=job.id, url=job_record.url, config=job_record.config
        )

        # process selected task.
        # currently only `transcribe` is supported.
        if job.type == dtos.JobType.transcript:
            result = strategy.transcribe()
        elif job.type == dtos.JobType.translation:
            result = strategy.translate()
        else:
            result = strategy.detect_language()

        artifact = models.Artifact(
            job_id=job.id, data=result, type=dtos.ArtifactType.raw_transcript
        )
        db.add(artifact)
        db.commit()

        update_job_status(db, job, dtos.JobStatus.success)
    except Exception as e:
        logger.error(e)
        update_job_status(db, job, dtos.JobStatus.error)
    finally:
        db.close()
