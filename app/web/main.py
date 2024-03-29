from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Path
from pydantic import AnyHttpUrl, BaseModel, Field
from sqlalchemy.orm import Session

import app.shared.db.models as models
import app.web.dtos as dtos
from app.web.injections.db import get_session
from app.web.injections.security import api_key_auth, sharing_auth
from app.web.injections.task_queue import get_task_queue
from app.web.task_queue import TaskQueue

DatabaseSession = Annotated[Session, Depends(get_session)]


def app_factory():
    app = FastAPI(
        description=(
            "whisperbox-transcribe is an async HTTP wrapper for openai/whisper."
        ),
        title="whisperbox-transcribe",
    )

    api_router = APIRouter(prefix="/api/v1")

    @api_router.get("/", status_code=204)
    def api_root():
        return None

    @api_router.get(
        "/jobs",
        dependencies=[Depends(api_key_auth)],
        response_model=list[dtos.Job],
        summary="Get metadata for all jobs",
    )
    def get_jobs(
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
        dependencies=[Depends(sharing_auth)],
        response_model=dtos.Job,
        summary="Get metadata for one job",
    )
    def get_job(
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
        dependencies=[Depends(api_key_auth)],
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
        dependencies=[Depends(sharing_auth)],
        status_code=204,
        summary="Delete a job with all artifacts",
    )
    def delete_transcript(
        session: DatabaseSession,
        id: UUID = Path(),
    ) -> None:
        """Remove metadata and artifacts for a single job."""
        session.query(models.Job).filter(models.Job.id == str(id)).delete()
        session.commit()
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
            default=None,
            description=(
                "Spoken language in the media file. "
                "While optional, this can improve output when set."
            ),
        )

    @api_router.post(
        "/jobs",
        dependencies=[Depends(api_key_auth)],
        response_model=dtos.Job,
        status_code=201,
        summary="Enqueue a new job",
    )
    def create_job(
        payload: PostJobPayload,
        session: DatabaseSession,
        task_queue: Annotated[TaskQueue, Depends(get_task_queue)],
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
            url=str(payload.url),
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
