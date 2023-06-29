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
from sqlalchemy import JSON, Column

import app.shared.db.models as models
from app.worker.strategies.base import BaseStrategy, TaskReturnValue


class DecodingOptions(BaseModel):
    """
    Options passed to the whipser model.
    This mirrors private type `whisper.DecodingOptions`.
    """

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

    def transcribe(self, job):
        result = self._run_whisper(
            self._download(job.url, job.id), "transcribe", job.config, job.id
        )

        return (models.ArtifactType.raw_transcript, result)

    def translate(self, job) -> TaskReturnValue:
        result = self._run_whisper(
            self._download(job.url, job.id),
            "translate",
            job.config,
            job.id,
        )
        return (models.ArtifactType.raw_transcript, result)

    def detect_language(self, job) -> TaskReturnValue:
        file = self._download(job.url, job.id)

        audio = whisper.pad_or_trim(whisper.load_audio(file))

        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
        _, probs = self.model.detect_language(mel)

        return (
            models.ArtifactType.language_detection,
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
        config: Column[JSON],
        job_id: UUID,
    ) -> list[Any]:
        try:
            result = self.model.transcribe(
                filepath,
                # turning this off might make the transcription less accurate,
                # but significantly reduces amount of model halucinations.
                condition_on_previous_text=False,
                **DecodingOptions(
                    task=task, language=config.language if config else None
                ).dict(),
            )

            return result["segments"]
        finally:
            self.cleanup(job_id)

    def _get_tmp_file(self, job_id: UUID) -> str:
        tmp = tempfile.gettempdir()
        return path.join(tmp, str(job_id))
