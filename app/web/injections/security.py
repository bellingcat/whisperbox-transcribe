from hmac import compare_digest
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.shared.settings import Settings
from app.web.injections.settings import get_settings


def api_key_auth(
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(HTTPBearer(auto_error=False))
    ],
    settings: Annotated[Settings, Depends(get_settings)],
):
    validate_credentials(credentials, settings.API_SECRET)


def sharing_auth(
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(HTTPBearer(auto_error=False))
    ],
    settings: Annotated[Settings, Depends(get_settings)],
):
    if settings.ENABLE_SHARING:
        pass
    else:
        validate_credentials(credentials, settings.API_SECRET)


def validate_credentials(credentials: HTTPAuthorizationCredentials, secret: str):
    # use compare_digest to counter timing attacks.
    if (
        not credentials
        or not secret
        or not compare_digest(secret, credentials.credentials)
    ):
        raise HTTPException(status_code=401)
