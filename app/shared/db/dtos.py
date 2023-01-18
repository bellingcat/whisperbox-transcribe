import enum
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Json


class ArtifactType(str, enum.Enum):
    raw_transcript = "raw_transcript"


class JobType(str, enum.Enum):
    transcript = "transcript"


class JobStatus(str, enum.Enum):
    create = "create"
    error = "error"
    success = "success"


class WithDbFields(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class Job(WithDbFields):
    status: JobStatus
    type: JobType
    url: AnyHttpUrl


class Artifact(WithDbFields):
    # TODO: narrow type
    data: Optional[Any]
    job_id: UUID
    type: ArtifactType
