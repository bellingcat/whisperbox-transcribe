import enum
import uuid

from pydantic import BaseModel, Field
from sqlalchemy import JSON, VARCHAR, Column, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declarative_base, declarative_mixin, declared_attr

Base = declarative_base()


# Enums


class JobType(str, enum.Enum):
    """Requested type of a job."""

    transcript = "transcribe"
    translation = "translate"
    language_detection = "detect_language"


class JobStatus(str, enum.Enum):
    """Processing status of a job."""

    create = "create"
    processing = "processing"
    error = "error"
    success = "success"


class ArtifactType(str, enum.Enum):
    raw_transcript = "transcript_raw"
    language_detection = "language_detection"


# JSON field types


class JobConfig(BaseModel):
    """(JSON) Configuration for a job."""

    language: str | None = Field(
        description=(
            "Spoken language in the media file. "
            "While optional, this can improve output."
        )
    )


class JobMeta(BaseModel):
    """(JSON) Metadata relating to a job's execution."""

    error: str | None = Field(
        description="Will contain a descriptive error message if processing failed."
    )

    task_id: uuid.UUID | None = Field(
        description="Internal celery id of this job submission."
    )


class RawTranscript(BaseModel):
    """(JSON) A single transcript passage returned by whisper."""

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

    language_code: str


# Sum type for all possible artifact data values
ArtifactData = list[RawTranscript] | LanguageDetection | None


@declarative_mixin
class WithStandardFields:
    """Mixin that adds standard fields (id, created_at, updated_at)."""

    @declared_attr
    def created_at(cls) -> Mapped[DateTime]:
        return Column(DateTime, server_default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls) -> Mapped[DateTime | None]:
        return Column(DateTime, onupdate=func.now())

    @declared_attr
    def id(cls) -> Mapped[UUID]:
        return Column(
            VARCHAR(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
        )


class Job(Base, WithStandardFields):
    __tablename__ = "jobs"

    url = Column(String(length=2048))
    status = Column(Enum(JobStatus), nullable=False)
    config = Column(JSON(none_as_null=True))
    meta = Column(JSON(none_as_null=True))
    type = Column(Enum(JobType), nullable=False)


class Artifact(Base, WithStandardFields):
    __tablename__ = "artifacts"

    job_id = Column(
        VARCHAR(36),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )

    data = Column(JSON(none_as_null=True))
    type = Column(Enum(ArtifactType), nullable=False)
