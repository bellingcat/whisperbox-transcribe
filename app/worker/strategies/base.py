from abc import ABC
from typing import Any, Protocol, Tuple
from uuid import UUID

import app.shared.db.models as models

TaskReturnValue = Tuple[models.ArtifactType, Any]


class TaskProtocol(Protocol):
    def __call__(self, job: models.Job) -> TaskReturnValue:
        ...


class BaseStrategy(ABC):
    def transcribe(self, job: models.Job) -> TaskReturnValue:
        raise NotImplementedError()

    def translate(self, job: models.Job) -> TaskReturnValue:
        raise NotImplementedError()

    def detect_language(self, job: models.Job) -> TaskReturnValue:
        raise NotImplementedError()

    def cleanup(self, job_id: UUID) -> None:
        raise NotImplementedError()
