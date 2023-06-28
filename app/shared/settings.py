import sys

from pydantic import BaseSettings


class Settings(BaseSettings):
    API_SECRET: str
    DATABASE_URI: str
    ENVIRONMENT: str

    TASK_SOFT_TIME_LIMIT: int = 3 * 60 * 60
    TASK_HARD_TIME_LIMIT: int = 4 * 60 * 60

    # derived settings
    BROKER_URL: str


if "pytest" in sys.modules:
    settings = Settings(
        _env_file=".env.test", _env_file_encoding="utf-8"
    )  # type: ignore
else:
    settings = Settings()  # type: ignore
