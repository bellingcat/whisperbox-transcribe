import os
import tempfile
from asyncio.log import logger
from os import path
from typing import Any, List, Literal, Optional
from uuid import UUID

import requests
import torch
from pydantic import BaseModel
from whisper import load_model

import app.shared.db.schemas as schemas


class DecodeOptions(BaseModel):
    language: Optional[str]
    task: Literal["translate", "transcribe"]


class LocalStrategy:
    def __init__(self) -> None:
        if torch.cuda.is_available():
            logger.info("initializing GPU model.")
            self.model = load_model(
                os.environ["WHISPER_MODEL"], download_root="/models"
            ).cuda()
        else:
            logger.info("initializing CPU model.")
            self.model = load_model(
                os.environ["WHISPER_MODEL"], download_root="/models"
            )

        logger.info("initialized local strategy.")

    def transcribe(
        self, url: str, job_id: UUID, config: Optional[schemas.JobConfig]
    ) -> List[Any]:
        return self.run_whisper(
            self._download(url, job_id), "transcribe", config, job_id
        )

    def translate(
        self, url: str, job_id: UUID, config: Optional[schemas.JobConfig]
    ) -> List[Any]:
        return self.run_whisper(
            self._download(url, job_id),
            "translate",
            config,
            job_id,
        )

    def detect_language(
        self, url: str, config: Optional[schemas.JobConfig]
    ) -> List[Any]:
        raise NotImplementedError("detect_language has not been implemented yet.")

    def _download(self, url: str, job_id: UUID) -> str:
        # re-create folder.
        filename = self._get_tmp_file(job_id)
        self._cleanup(job_id)

        # stream media to disk.
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        return filename

    def run_whisper(
        self,
        filepath: str,
        task: str,
        config: Optional[schemas.JobConfig],
        job_id: UUID,
    ) -> List[Any]:
        try:
            language = config.language if config else None

            result = self.model.transcribe(
                filepath,
                condition_on_previous_text=False,
                **DecodeOptions(task=task, language=language).dict(),
            )

            return result["segments"]
        finally:
            self._cleanup(job_id)

    def _get_tmp_file(self, job_id: UUID) -> str:
        tmp = tempfile.gettempdir()
        return path.join(tmp, str(job_id))

    def _cleanup(self, job_id: UUID) -> None:
        try:
            os.remove(self._get_tmp_file(job_id))
        except OSError:
            pass
