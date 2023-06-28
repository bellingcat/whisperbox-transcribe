from asyncio.log import logger
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path
from sqlalchemy import or_
from sqlalchemy.orm import Session

import app.shared.db.models as models
import app.shared.db.schemas as schemas
from app.shared.celery import get_celery_binding
from app.shared.db.base import get_session
from app.web.dtos import DEFAULT_RESPONSES, DetailResponse, PostJobPayload
from app.web.security import authenticate_api_key

app = FastAPI(
    description="whisperbox-transcribe is an async HTTP wrapper for openai/whisper.",
    title="whisperbox-transcribe",
)
celery = get_celery_binding()


def queue_task(job: models.Job) -> None:
    # queue an async transcription task.
    # we use a signature here to allow full separation of
    # worker processes and dependencies.
    transcribe = celery.signature("app.worker.main.transcribe")
    # TODO: catch delivery errors.
    transcribe.delay(job.id)


api_router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(authenticate_api_key)],
    responses={**DEFAULT_RESPONSES},
)


@api_router.get("/", response_model=None, status_code=204)
def api_root() -> None:
    return None


@api_router.post(
    "/jobs",
    response_model=schemas.Job,
    status_code=201,
    summary="Enqueue a new job",
)
def create_job(
    payload: PostJobPayload,
    session: Session = Depends(get_session),
) -> models.Job:
    """
    Enqueue a new whisper job for processing.
    Notes:
     * Jobs are processed one-by-one in order of creation.
     * `payload.url` needs to point directly to a media file.
     * The media file is downloaded to a tmp file for the duration of processing.
       enough free space needs to be available on disk.
     * Media files ideally are audio files with a sampling rate of 16kHz.
       other files will be transcoded automatically via ffmpeg which might
       consume considerable resources while active.
     * Once a job is created, you can query its status by its id.
    """
    # create a job with status "create" and save it to the database.
    job = models.Job(
        url=payload.url,
        status=schemas.JobStatus.create,
        type=payload.type,
        config={"language": payload.language} if payload.language else None,
    )

    session.add(job)
    session.commit()

    # queue an async transcription task.
    # we use a signature here to allow full separation of
    # worker processes and dependencies.
    transcribe = celery.signature("app.worker.main.transcribe")
    # TODO: catch delivery errors.
    transcribe.delay(job.id)

    return job


@api_router.get(
    "/jobs", response_model=List[schemas.Job], summary="Get metadata for all jobs"
)
def get_transcripts(
    type: Optional[schemas.JobType] = None, session: Session = Depends(get_session)
) -> List[models.Job]:
    """Get metadata for all jobs."""
    query = session.query(models.Job)

    if type:
        query = query.filter(models.Job.type == type)

    return query.all()


@api_router.get(
    "/jobs/{id}",
    response_model=schemas.Job,
    responses={404: {"model": DetailResponse, "description": "Not found"}},
    summary="Get metadata for one job",
)
def get_transcript(
    id: UUID = Path(), session: Session = Depends(get_session)
) -> Optional[models.Job]:
    """
    Use this route to check transcription status of any given job.
    """
    job = session.query(models.Job).filter(models.Job.id == str(id)).one_or_none()
    if not job:
        raise HTTPException(status_code=404)
    return job


@api_router.get(
    "/jobs/{id}/artifacts",
    response_model=List[schemas.Artifact],
    summary="Get all artifacts for one job",
)
def get_artifacts_for_job(
    id: UUID = Path(), session: Session = Depends(get_session)
) -> List[models.Artifact]:
    """
    Right now, there is only one type of artifact (`raw_transcript`).
    Returns an empty array for unfinished or non-existant jobs.
    """
    artifacts = (
        session.query(models.Artifact).filter(models.Artifact.job_id == str(id))
    ).all()

    return artifacts


@api_router.delete(
    "/jobs/{id}", status_code=204, summary="Delete a job with all artifacts"
)
def delete_transcript(
    id: UUID = Path(), session: Session = Depends(get_session)
) -> None:
    """Remove metadata and artifacts for a single job."""
    session.query(models.Job).filter(models.Job.id == str(id)).delete()
    return None


app.include_router(api_router)


# TODO: we could use `acks_late` to handle this scenario within celery itself.
# the reason this does not work well in our case is that `visibility_timeout`
# needs to be very high since whisper workers can be long running.
# doing this application-side bears the risk of poison pilling the worker though,
# implement a workaround with an acceptable trade-off. (=> retry only once?)
@app.on_event("startup")
def on_startup() -> None:
    session = get_session().__next__()

    jobs = (
        session.query(models.Job)
        .filter(
            or_(
                models.Job.status == schemas.JobStatus.processing,
                models.Job.status == schemas.JobStatus.create,
            )
        )
        .order_by(models.Job.created_at)
    ).all()

    logger.info(f"Requeueing {len(jobs)} jobs.")
    for job in jobs:
        queue_task(job)
