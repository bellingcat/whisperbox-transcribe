from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound

from .db.base import get_db
from .db.models import Account

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def authenticate_api_key(
    db: Session = Depends(get_db),
    api_key: str = Depends(oauth2_scheme),
) -> Account:
    try:
        account = db.query(Account).filter(Account.api_key == UUID(api_key)).one()
    except NoResultFound:
        raise HTTPException(status_code=401)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=422)

    return account
