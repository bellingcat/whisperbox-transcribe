import os
import shutil
import tempfile
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

    def transcribe(self) -> List[Any]:
        result = self.run_whisper(self._download(), "transcribe")
        self._cleanup()
        return result

    def translate(self) -> List[Any]:
        result = self.run_whisper(self._download(), "translate")
        self._cleanup()
        return result

    def detect_language(self) -> List[Any]:
        raise NotImplementedError("detect_language has not been implemented yet.")

    def _download(self) -> str:
        dirname = self._get_tmp_dir()
        filename = path.join(dirname, "media.mp3")

        # re-create folder.
        shutil.rmtree(dirname, ignore_errors=True)
        os.makedirs(dirname)

        # stream media to disk.
        with requests.get(self.url, stream=True) as r:
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        return filename

    def run_whisper(self, filepath: str, task: str) -> List[Any]:
        language = self.config.language if self.config else None
        decode_opts = DecodeOptions(task=task, language=language)
        model = load_model("small", download_root="/models")

        result = model.transcribe(
            filepath, condition_on_previous_text=False, **decode_opts.dict()
        )

        return result["segments"]

    def _get_tmp_dir(self) -> str:
        return path.join(tempfile.gettempdir(), str(self.job_id))

    def _cleanup(self) -> None:
        shutil.rmtree(self._get_tmp_dir(), ignore_errors=True)

    def _convert(self) -> None:
        pass

    def _transcribe(self) -> None:
        pass
