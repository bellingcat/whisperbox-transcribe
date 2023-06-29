import os
import tempfile
from asyncio.log import logger
from os import path
from typing import Any, Literal
from uuid import UUID

import requests
import torch
import whisper
from pydantic import BaseModel

import app.shared.db.schemas as schemas
from app.worker.strategies.base import BaseStrategy, TaskReturnValue


class DecodeOptions(BaseModel):
    language: str | None
    task: Literal["translate", "transcribe"]


class LocalStrategy(BaseStrategy):
    def __init__(self) -> None:
        if torch.cuda.is_available():
            logger.info("initializing GPU model.")
            self.model = whisper.load_model(
                os.environ["WHISPER_MODEL"], download_root="/models"
            ).cuda()
        else:
            logger.info("initializing CPU model.")
            self.model = whisper.load_model(
                os.environ["WHISPER_MODEL"], download_root="/models"
            )

        logger.info("initialized local strategy.")

    def cleanup(self, job_id) -> None:
        try:
            os.remove(self._get_tmp_file(job_id))
        except OSError:
            pass

    def transcribe(self, url, job_id, config):
        return (
            schemas.ArtifactType.raw_transcript,
            self._run_whisper(
                self._download(url, job_id), "transcribe", config, job_id
            ),
        )

    def translate(self, url, job_id, config) -> TaskReturnValue:
        return (
            schemas.ArtifactType.raw_transcript,
            self._run_whisper(
                self._download(url, job_id),
                "translate",
                config,
                job_id,
            ),
        )

    def detect_language(self, url, job_id, config) -> TaskReturnValue:
        file = self._download(url, job_id)

        audio = whisper.pad_or_trim(whisper.load_audio(file))

        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
        _, probs = self.model.detect_language(mel)

        return (
            schemas.ArtifactType.language_detection,
            {"code": max(probs, key=probs.get)},
        )

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

    def _run_whisper(
        self,
        filepath: str,
        task: Literal["translate", "transcribe"],
        config: schemas.JobConfig | None,
        job_id: UUID,
    ) -> list[Any]:
        try:
            language = config.language if config else None

            result = self.model.transcribe(
                filepath,
                condition_on_previous_text=False,
                **DecodeOptions(task=task, language=language).dict(),
            )

            return result["segments"]
        finally:
            self.cleanup(job_id)

    def _get_tmp_file(self, job_id: UUID) -> str:
        tmp = tempfile.gettempdir()
        return path.join(tmp, str(job_id))
