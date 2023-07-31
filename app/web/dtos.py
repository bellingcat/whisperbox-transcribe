from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict

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
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class Job(WithDbFields):
    """A transcription job for one media file."""

    status: JobStatus
    type: JobType
    url: AnyHttpUrl
    meta: JobMeta | None = None
    config: JobConfig | None = None


class Artifact(WithDbFields):
    job_id: UUID
    data: ArtifactData
    type: ArtifactType
