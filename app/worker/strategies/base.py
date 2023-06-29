import os
import tempfile
from abc import ABC
from typing import Any, Protocol, Tuple
from uuid import UUID

import requests

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
        try:
            os.remove(self._get_tmp_file(job_id))
        except OSError:
            pass

    def _get_tmp_file(self, job_id: UUID) -> str:
        tmp = tempfile.gettempdir()
        return os.path.join(tmp, str(job_id))

    def _download(self, url: str, job_id: UUID) -> str:
        # re-create folder.
        filename = self._get_tmp_file(job_id)
        self.cleanup(job_id)

        # stream media to disk.
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        return filename
