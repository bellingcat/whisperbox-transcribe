from hmac import compare_digest

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.shared.settings import settings


def authenticate_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> None:
    # use compare_digest to counter timing attacks.
    if not credentials or not compare_digest(
        settings.API_SECRET, credentials.credentials
    ):
        raise HTTPException(status_code=401)
