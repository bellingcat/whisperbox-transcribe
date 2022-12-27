from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class WithStandardFields(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class AccountBase(BaseModel):
    api_key: UUID
    name: str


class Account(AccountBase, WithStandardFields):
    pass
