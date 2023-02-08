import enum
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel


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
    create = "create"
    processing = "processing"
    error = "error"
    success = "success"


class JobConfig(BaseModel):
    language: Optional[str]


class JobMeta(BaseModel):
    error: Optional[str]
    task_id: Optional[UUID]


class Job(WithDbFields):
    status: JobStatus
    type: JobType
    url: AnyHttpUrl
    meta: Optional[JobMeta]
    config: Optional[JobConfig]


class Artifact(WithDbFields):
    # TODO: narrow type
    data: Optional[List[Any]]
    job_id: UUID
    type: ArtifactType
