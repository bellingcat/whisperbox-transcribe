from hmac import compare_digest

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def authenticate_api_key(token: str = Depends(oauth2_scheme)) -> None:
    if not token:
        raise HTTPException(status_code=422)
    # use compare_digest to counter timing attacks.
    if not compare_digest(settings.API_SECRET, token):
        raise HTTPException(status_code=401)
