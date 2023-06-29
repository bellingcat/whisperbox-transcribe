from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Field

from app.shared.db.models import ArtifactType, JobStatus, JobType

# JSON field types


class JobConfig(BaseModel):
    """Configuration for a job."""

    language: str | None = Field(
        description=(
            "Spoken language in the media file. "
            "While optional, this can improve output."
        )
    )


class JobMeta(BaseModel):
    """Metadata relating to a job's execution."""

    error: str | None = Field(
        description="Will contain a descriptive error message if processing failed."
    )

    task_id: UUID | None = Field(
        description="Internal celery id of this job submission."
    )


class RawTranscript(BaseModel):
    """A single transcript passage returned by whisper."""

    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: list[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float


class LanguageDetection(BaseModel):
    """A language detection"""

    code: str


# DB objects


class WithDbFields(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime | None

    class Config:
        orm_mode = True


class Job(WithDbFields):
    """A transcription job for one media file."""

    status: JobStatus
    type: JobType
    url: AnyHttpUrl
    meta: JobMeta | None
    config: JobConfig | None


class Artifact(WithDbFields):
    job_id: UUID
    data: LanguageDetection | RawTranscript | None
    type: ArtifactType
