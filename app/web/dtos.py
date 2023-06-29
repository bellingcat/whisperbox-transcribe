from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel

from app.shared.db.models import (
    ArtifactData,
    ArtifactType,
    JobConfig,
    JobMeta,
    JobStatus,
    JobType,
)

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
    data: ArtifactData
    type: ArtifactType
