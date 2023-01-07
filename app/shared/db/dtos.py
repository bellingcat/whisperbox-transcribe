import enum
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Json


class ArtifactType(enum.Enum):
    RawTranscript = "RawTranscript"


class JobType(enum.Enum):
    Transcript = "Transcript"


class JobStatus(enum.Enum):
    Create = "Create"
    Error = "Error"
    Success = "Success"


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
    data: Optional[Json]
    job_id: UUID
    type: ArtifactType
