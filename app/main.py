from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path
from pydantic import AnyHttpUrl, BaseModel
from sqlalchemy.orm import Session
from app.db.base import get_session

from app.db.dtos import Job, JobStatus, JobType
import app.db.models as models

from .security import authenticate_api_key

app = FastAPI()

api_router = APIRouter(prefix="/api/v1", dependencies=[Depends(authenticate_api_key)])


@api_router.get("/")
def api_root() -> Dict:
    return {}


class TranscriptPayload(BaseModel):
    url: AnyHttpUrl


@api_router.post("/transcripts", response_model=Job)
def create_transcript(
    payload: TranscriptPayload, session: Session = Depends(get_session)
) -> models.Job:
    job = models.Job(url=payload.url, status=JobStatus.Create, type=JobType.Transcript)
    session.add(job)
    session.flush()
    return job


@api_router.get("/transcripts", response_model=List[Job])
def get_transcripts(session: Session = Depends(get_session)) -> List[models.Job]:
    return session.query(models.Job).filter(models.Job.type == JobType.Transcript).all()


@api_router.get("/transcripts/{id}", response_model=Job)
def get_transcript(
    id: UUID = Path(), session: Session = Depends(get_session)
) -> Optional[Job]:
    job = (
        session.query(models.Job)
        .filter(models.Job.id == id)
        .filter(models.Job.type == JobType.Transcript)
        .one_or_none()
    )
    if not job:
        raise HTTPException(status_code=404)
    return job


@api_router.delete("/transcripts/{id}")
def delete_transcript(
    id: UUID = Path(), session: Session = Depends(get_session)
) -> None:
    session.query(models.Job).filter(models.Job.id == id).filter(
        models.Job.type == JobType.Transcript
    ).delete()
    return None


app.include_router(api_router)
