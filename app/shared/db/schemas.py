import enum
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Field


class WithDbFields(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class ArtifactType(str, enum.Enum):
    raw_transcript = "raw_transcript"


class JobType(str, enum.Enum):
    transcript = "transcript"
    translation = "translation"
    language_detection = "language_detection"


class JobStatus(str, enum.Enum):
    """Processing status of a job."""

    create = "create"
    processing = "processing"
    error = "error"
    success = "success"


class JobConfig(BaseModel):
    """Configuration for a job."""

    # TODO: limit to locales selected by whisper.
    language: Optional[str] = Field(
        description=(
            "Spoken language in the media file."
            "While optional, this can improve output "
            "by selecting a language-specific model. (applies to 'en')"
        )
    )


class JobMeta(BaseModel):
    """Metadata relating to a job's execution."""

    error: Optional[str] = Field(
        description="Will contain a descriptive error message if processing failed."
    )
    task_id: Optional[UUID] = Field(
        description="Internal celery id of this job submission."
    )


class Job(WithDbFields):
    """A transcription job for one media file."""

    status: JobStatus
    type: JobType
    url: AnyHttpUrl
    meta: Optional[JobMeta]
    config: Optional[JobConfig]


class RawTranscript(BaseModel):
    """A single transcript passage returned by whisper."""

    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: List[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float


class Artifact(WithDbFields):
    """whisper output for one job."""

    data: Optional[List[RawTranscript]]
    job_id: UUID
    type: ArtifactType
