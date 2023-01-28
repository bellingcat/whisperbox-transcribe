import os
import tempfile
from asyncio.log import logger
from os import path
from typing import Any, List, Literal, Optional
from uuid import UUID

import requests
from pydantic import BaseModel
from sqlalchemy.orm import Session
from whisper import load_model

import app.shared.db.dtos as dtos


class DecodeOptions(BaseModel):
    language: Optional[str]
    task: Literal["translate", "transcribe"]


class LocalStrategy:
    def __init__(
        self, db: Session, job_id: UUID, url: str, config: Optional[dtos.JobConfig]
    ):
        self.db = db
        self.job_id = job_id
        self.url = url
        self.config = config
        logger.info(f"[{self.job_id}]: initialized local strategy.")

    def transcribe(self) -> List[Any]:
        return self.run_whisper(self._download(), "transcribe")

    def translate(self) -> List[Any]:
        return self.run_whisper(self._download(), "translate")

    def detect_language(self) -> List[Any]:
        raise NotImplementedError("detect_language has not been implemented yet.")

    def _download(self) -> str:
        # re-create folder.
        filename = self._get_tmp_file()
        self._cleanup()

        # stream media to disk.
        with requests.get(self.url, stream=True) as r:
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        return filename

    def run_whisper(self, filepath: str, task: str) -> List[Any]:
        try:
            language = self.config.language if self.config else None
            model = load_model("small", download_root="/models")

            result = model.transcribe(
                filepath,
                condition_on_previous_text=False,
                **DecodeOptions(task=task, language=language).dict(),
            )

            return result["segments"]
        finally:
            self._cleanup()

    def _get_tmp_file(self) -> str:
        tmp = tempfile.gettempdir()
        return path.join(tmp, str(self.job_id))

    def _cleanup(self) -> None:
        try:
            os.remove(self._get_tmp_file())
        except OSError:
            pass

    def _convert(self) -> None:
        pass

    def _transcribe(self) -> None:
        pass
