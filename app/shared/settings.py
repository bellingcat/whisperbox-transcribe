import sys

from pydantic import BaseSettings


class Settings(BaseSettings):
    API_SECRET: str
    BROKER_URL: str
    DATABASE_URI: str
    ENVIRONMENT: str

    TASK_SOFT_TIME_LIMIT: int = 3 * 60 * 60
    TASK_HARD_TIME_LIMIT: int = 4 * 60 * 60

    ENABLE_SHARING: bool = False


if "pytest" in sys.modules:
    settings = Settings(_env_file=".env.test")  # type: ignore
else:
    settings = Settings()  # type: ignore
