from typing import Any
from uuid import UUID

from celery import Task
from sqlalchemy.orm import Session

import app.shared.db.models as models
from app.shared.celery import get_celery_binding
from app.shared.db.base import make_engine, make_session_local
from app.shared.logger import logger
from app.shared.settings import Settings
from app.worker.strategies.local import LocalStrategy

# TODO: refactor to be part of a Task instance.
settings = Settings()  # type: ignore
celery = get_celery_binding(settings.BROKER_URL)
engine = make_engine(settings.DATABASE_URI)
SessionLocal = make_session_local(engine)


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
    task_acks_late=True,
    task_acks_on_failure_or_timeout=True,
    task_reject_on_worker_lost=True,
)
def transcribe(self: TranscribeTask, job_id: UUID) -> None:
    session: Session | None = None
    job: models.Job | None = None

    try:
        if not self.strategy:
            raise Exception("expected a transcription strategy to be defined.")

        # runs in a separate thread => requires sqlite's WAL mode to be enabled.
        session = SessionLocal()

        # work around mypy not inferring the sum type correctly.
        if not session:
            raise Exception("failed to acquire a session.")

        # check if passed job should be processed.

        job = session.query(models.Job).filter(models.Job.id == job_id).one_or_none()

        if job is None:
            logger.warn("[{job.id}]: Received unknown job, abort.")
            return

        if job.status in [models.JobStatus.error, models.JobStatus.success]:
            logger.warn("[{job.id}]: job has already been processed, abort.")
            return

        logger.debug(f"[{job.id}]: start processing {job.type} job.")

        if job.meta is not None:
            attempts = 1 + (job.meta.get("attempts") or 0)
        else:
            attempts = 1

        # SAFEGUARD: celery's retry policies do not handle lost workers, retry once.
        # @see https://github.com/celery/celery/pull/6103
        if attempts > 2:
            raise Exception("Maximum number of retries exceeded for killed worker.")

        # unit of work: set task status to processing.

        job.meta = {"task_id": self.request.id, "attempts": attempts}

        job.status = models.JobStatus.processing
        session.commit()

        logger.debug(f"[{job.id}]: finished setting task to {job.status}.")

        # unit of work: process job with whisper.
        result_type, result = self.strategy.process(job)
        logger.debug(f"[{job.id}]: successfully processed audio.")

        artifact = models.Artifact(job_id=str(job.id), data=result, type=result_type)
        session.add(artifact)

        job.status = models.JobStatus.success
        session.commit()

        logger.debug(f"[{job.id}]: successfully stored artifact.")

    except Exception as e:
        if job and session:
            if session.in_transaction():
                session.rollback()
            if job.meta is not None:
                job.meta = {**job.meta, "error": str(e)}
            else:
                job.meta = {"error": str(e)}

            job.status = models.JobStatus.error
            session.commit()
        raise
    finally:
        if self.strategy:
            self.strategy.cleanup(job_id)
        if session:
            session.close()
