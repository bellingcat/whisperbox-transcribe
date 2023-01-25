from time import sleep
from uuid import UUID

from celery import Celery
from sqlalchemy.orm import Session

import app.shared.db.dtos as dtos
import app.shared.db.models as models
from app.shared.config import settings
from app.shared.db.base import SessionLocal

celery = Celery(__name__)

celery.conf.broker_url = settings.BROKER_URI


def update_job_status(db: Session, job_id: UUID, status: dtos.JobStatus) -> None:
    db.begin()
    job = db.query(models.Job).filter(models.Job.id == job_id).one()
    job.status = status
    db.commit()


@celery.task()
def transcribe(job_id: UUID) -> int:
    try:
        db: Session = SessionLocal()
        update_job_status(db, job_id, dtos.JobStatus.processing)
        sleep(60)
        update_job_status(db, job_id, dtos.JobStatus.success)
        db.commit()
    except Exception:
        update_job_status(db, job_id, dtos.JobStatus.error)
    finally:
        db.close()

    return 0
