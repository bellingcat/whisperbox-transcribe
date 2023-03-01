from typing import Any, Dict, Optional, Union

from pydantic import AnyHttpUrl, BaseModel, Field

import app.shared.db.schemas as schemas


class DetailResponse(BaseModel):
    detail: str


DEFAULT_RESPONSES: Dict[Union[int, str], Dict[str, Any]] = {
    401: {"model": DetailResponse, "description": "Not authenticated"}
}


class PostJobPayload(BaseModel):
    url: AnyHttpUrl = Field(
        description=(
            "URL where the media file is available. This needs to be a direct link."
        )
    )

    type: schemas.JobType = Field(
        description="""Type of this job.
        `transcript` uses the original language of the audio.
        `translation` creates an automatic translation to english.
        `language_detection` detects language from the first 30 seconds of audio."""
    )

    # TODO: limit to locales selected by whisper.
    language: Optional[str] = Field(
        description=(
            "Spoken language in the media file. "
            "While optional, this can improve output when set."
        )
    )
