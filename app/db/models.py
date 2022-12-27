from typing import Optional
import uuid

from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_mixin, declared_attr, Mapped
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


@declarative_mixin
class WithStandardFields:
    @declared_attr
    def created_at(cls) -> Mapped[DateTime]:
        return Column(DateTime, server_default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls) -> Mapped[Optional[DateTime]]:
        return Column(DateTime, onupdate=func.now())

    @declared_attr
    def id(cls) -> Mapped[UUID]:
        return Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)


class Account(Base, WithStandardFields):
    __tablename__ = "accounts"

    api_key = Column(UUID(as_uuid=True), index=True, default=uuid.uuid4)
    name = Column(String(length=256), unique=True)
