import os
from asyncio.log import logger
from typing import Any, Literal
from uuid import UUID

import torch
import whisper
from pydantic import BaseModel

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
            logger.debug("initializing GPU model.")
            self.model = whisper.load_model(
                os.environ["WHISPER_MODEL"], download_root="/models"
            ).cuda()
        else:
            logger.debug("initializing CPU model.")
            self.model = whisper.load_model(
                os.environ["WHISPER_MODEL"], download_root="/models"
            )

        logger.debug("initialized local strategy.")

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

        # see: https://github.com/openai/whisper/blob/248b6cb124225dd263bb9bd32d060b6517e067f8/README.md?plain=1#L114
        audio = whisper.pad_or_trim(whisper.load_audio(file))
        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
        _, probs = self.model.detect_language(mel)

        return (
            models.ArtifactType.language_detection,
            {"code": max(probs, key=probs.get)},
        )

    def _run_whisper(
        self,
        filepath: str,
        task: Literal["translate", "transcribe"],
        config: dict[str, Any],
        job_id: UUID,
    ) -> list[Any]:
        result = self.model.transcribe(
            filepath,
            # turning this off might make the transcription less accurate,
            # but significantly reduces amount of model halucinations.
            condition_on_previous_text=False,
            **DecodingOptions(
                task=task,
                language=models.JobConfig(**config).language if config else None,
            ).dict(),
        )

        return result["segments"]
