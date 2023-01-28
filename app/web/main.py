from asyncio.log import logger
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path
from pydantic import AnyHttpUrl, BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

import app.shared.db.dtos as dtos
import app.shared.db.models as models
from app.shared.celery import get_celery_binding
from app.shared.db.base import get_session
from app.web.security import authenticate_api_key

app = FastAPI()
celery = get_celery_binding()

api_router = APIRouter(prefix="/api/v1", dependencies=[Depends(authenticate_api_key)])


def queue_task(job: models.Job) -> None:
    # queue an async transcription task.
    # we use a signature here to allow full separation of
    # worker processes and dependencies.
    transcribe = celery.signature("app.worker.main.transcribe")
    # TODO: catch delivery errors.
    transcribe.delay(job.id)


@api_router.get("/")
def api_root() -> Dict:
    return {}


class PostJobPayload(BaseModel):
    url: AnyHttpUrl
    type: dtos.JobType
    language: Optional[str]


@api_router.post("/jobs", response_model=dtos.Job, status_code=201)
def create_job(
    payload: PostJobPayload,
    session: Session = Depends(get_session),
) -> models.Job:
    # create a job with status "create" and save it to the database.
    job = models.Job(
        url=payload.url,
        status=dtos.JobStatus.create,
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


@api_router.get("/jobs", response_model=List[dtos.Job])
def get_transcripts(
    type: Optional[dtos.JobType] = None, session: Session = Depends(get_session)
) -> List[models.Job]:
    query = session.query(models.Job)

    if type:
        query = query.filter(models.Job.type == type)

    return query.all()


@api_router.get("/jobs/{id}", response_model=dtos.Job)
def get_transcript(
    id: UUID = Path(), session: Session = Depends(get_session)
) -> Optional[models.Job]:
    job = session.query(models.Job).filter(models.Job.id == id).one_or_none()
    if not job:
        raise HTTPException(status_code=404)
    return job


@api_router.get("/jobs/{id}/artifacts", response_model=List[dtos.Artifact])
def get_artifacts_for_job(
    id: UUID = Path(), session: Session = Depends(get_session)
) -> List[models.Artifact]:
    artifacts = (
        session.query(models.Artifact).filter(models.Artifact.job_id == id)
    ).all()

    if not len(artifacts):
        raise HTTPException(status_code=404)

    return artifacts


@api_router.delete("/jobs/{id}", status_code=204)
def delete_transcript(
    id: UUID = Path(), session: Session = Depends(get_session)
) -> None:
    session.query(models.Job).filter(models.Job.id == id).delete()
    return None


app.include_router(api_router)

# TODO:
# we could use `acks_late` to handle this scenario within celery itself.
# the reason this does not work well in our case is that `visibility_timeout`
# needs to be very high since whisper workers can be long running.
# doing this application-side bears the risk of poison pilling the worker though,
# implement a workaround with an acceptable trade-off. (=> retry only once?)
@app.on_event("startup")
def on_startup() -> None:
    session = get_session().__next__()

    jobs = (
        session.query(models.Job)
            .filter(or_(models.Job.status == dtos.JobStatus.processing, models.Job.status == dtos.JobStatus.create))
            .order_by(models.Job.created_at)
    ).all()

    logger.info(f"Re-queueing {len(jobs)} jobs.")
    for job in jobs:
        queue_task(job)
