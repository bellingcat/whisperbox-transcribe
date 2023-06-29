from contextlib import asynccontextmanager
from typing import Annotated, Callable, Generator
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path
from pydantic import AnyHttpUrl, BaseModel, Field
from sqlalchemy.orm import Session

import app.shared.db.models as models
import app.web.dtos as dtos
from app.shared.db.base import SessionLocal
from app.shared.settings import settings
from app.web.security import authenticate_api_key
from app.web.task_queue import TaskQueue


def app_factory(
    session_getter: Callable[[], Generator[Session, None, None]]
) -> FastAPI:
    DatabaseSession = Annotated[Session, Depends(session_getter)]

    task_queue = TaskQueue()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        with SessionLocal() as session:
            task_queue.rehydrate(session)
        yield

    app = FastAPI(
        description=(
            "whisperbox-transcribe is an async HTTP wrapper for openai/whisper."
        ),
        lifespan=lifespan,
        title="whisperbox-transcribe",
    )

    api_router = APIRouter(prefix="/api/v1")

    @api_router.get("/", response_model=None, status_code=204)
    def api_root() -> None:
        return None

    @api_router.get(
        "/jobs",
        dependencies=[Depends(authenticate_api_key)],
        response_model=list[dtos.Job],
        summary="Get metadata for all jobs",
    )
    def get_transcripts(
        session: DatabaseSession,
        type: dtos.JobType | None = None,
    ) -> list[models.Job]:
        """Get metadata for all jobs."""
        query = session.query(models.Job).order_by(models.Job.created_at.desc())

        if type:
            query = query.filter(models.Job.type == type)

        return query.all()

    @api_router.get(
        "/jobs/{id}",
        dependencies=[] if settings.ENABLE_SHARING else [Depends(authenticate_api_key)],
        response_model=dtos.Job,
        summary="Get metadata for one job",
    )
    def get_transcript(
        session: DatabaseSession,
        id: UUID = Path(),
    ) -> models.Job | None:
        """
        Use this route to check transcription status of any given job.
        """
        job = session.query(models.Job).filter(models.Job.id == str(id)).one_or_none()

        if not job:
            raise HTTPException(status_code=404)

        return job

    @api_router.get(
        "/jobs/{id}/artifacts",
        dependencies=[] if settings.ENABLE_SHARING else [Depends(authenticate_api_key)],
        response_model=list[dtos.Artifact],
        summary="Get all artifacts for one job",
    )
    def get_artifacts_for_job(
        session: DatabaseSession,
        id: UUID = Path(),
    ) -> list[models.Artifact]:
        """
        Returns all artifacts for one job.
        See the type of `data` for possible data types.
        Returns an empty array for unfinished or non-existant jobs.
        """
        artifacts = (
            session.query(models.Artifact).filter(models.Artifact.job_id == str(id))
        ).all()

        return artifacts

    @api_router.delete(
        "/jobs/{id}",
        dependencies=[Depends(authenticate_api_key)],
        status_code=204,
        summary="Delete a job with all artifacts",
    )
    def delete_transcript(
        session: DatabaseSession,
        id: UUID = Path(),
    ) -> None:
        """Remove metadata and artifacts for a single job."""
        session.query(models.Job).filter(models.Job.id == str(id)).delete()
        return None

    class PostJobPayload(BaseModel):
        url: AnyHttpUrl = Field(
            description=(
                "URL where the media file is available. This needs to be a direct link."
            )
        )

        type: models.JobType = Field(
            description="""Type of this job.
            `transcript` uses the original language of the audio.
            `translation` creates an automatic translation to english.
            `language_detection` detects language from the first 30 seconds of audio."""
        )

        language: str | None = Field(
            description=(
                "Spoken language in the media file. "
                "While optional, this can improve output when set."
            )
        )

    @api_router.post(
        "/jobs",
        dependencies=[Depends(authenticate_api_key)],
        response_model=dtos.Job,
        status_code=201,
        summary="Enqueue a new job",
    )
    def create_job(
        payload: PostJobPayload,
        session: DatabaseSession,
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
            status=dtos.JobStatus.create,
            type=payload.type,
            config={"language": payload.language} if payload.language else None,
        )

        session.add(job)
        session.commit()

        task_queue.queue_task(job)

        return job

    app.include_router(api_router)

    return app
