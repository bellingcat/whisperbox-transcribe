from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path
from pydantic import AnyHttpUrl, BaseModel
from sqlalchemy.orm import Session

import app.shared.db.dtos as dtos
import app.shared.db.models as models
from app.shared.db.base import get_session
from app.web.security import authenticate_api_key
from app.worker.main import transcribe

app = FastAPI()

api_router = APIRouter(prefix="/api/v1", dependencies=[Depends(authenticate_api_key)])


@api_router.get("/")
def api_root() -> Dict:
    return {}


class TranscriptPayload(BaseModel):
    url: AnyHttpUrl
    type: dtos.JobType


@api_router.post("/jobs", response_model=dtos.Job, status_code=201)
def create_job(
    payload: TranscriptPayload, session: Session = Depends(get_session)
) -> models.Job:
    job = models.Job(url=payload.url, status=dtos.JobStatus.create, type=payload.type)
    session.add(job)
    session.flush()

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
