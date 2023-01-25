import sys

from pydantic import BaseSettings


class Settings(BaseSettings):
    API_SECRET: str
    DATABASE_URI: str
    ENVIRONMENT: str

    # derived settings
    BROKER_URI: str


if "pytest" in sys.modules:
    settings = Settings(_env_file=".env.test", _env_file_encoding="utf-8")  # type: ignore
else:
    settings = Settings()
