import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    DATABASE_URI: str
    ENVIRONMENT: str
    API_SECRET: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


if "ENVIRONMENT" in os.environ and os.environ["ENVIRONMENT"] == "test":
    settings = Settings(_env_file=".env.test")  # type: ignore
else:
    settings = Settings()
