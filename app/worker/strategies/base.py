from abc import ABC
from typing import Any, Protocol, Tuple
from uuid import UUID

import app.shared.db.models as models
import app.shared.db.schemas as schemas

TaskReturnValue = Tuple[models.ArtifactType, Any]


class TaskProtocol(Protocol):
    def __call__(
        self, url: str, job_id: UUID, config: schemas.JobConfig | None
    ) -> TaskReturnValue:
        ...


class BaseStrategy(ABC):
    def transcribe(
        self, url: str, job_id: UUID, config: schemas.JobConfig | None
    ) -> TaskReturnValue:
        raise NotImplementedError()

    def translate(
        self, url: str, job_id: UUID, config: schemas.JobConfig | None
    ) -> TaskReturnValue:
        raise NotImplementedError()

    def detect_language(
        self, url: str, job_id: UUID, config: schemas.JobConfig | None
    ) -> TaskReturnValue:
        raise NotImplementedError()

    def cleanup(self, job_id: UUID) -> None:
        raise NotImplementedError()
