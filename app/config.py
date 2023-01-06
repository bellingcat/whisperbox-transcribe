import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    API_SECRET: str
    DATABASE_URI: str
    ENVIRONMENT: str
    REDIS_URI: str


if "ENVIRONMENT" in os.environ and os.environ["ENVIRONMENT"] == "test":
    settings = Settings(_env_file=".env.test")  # type: ignore
else:
    settings = Settings()
