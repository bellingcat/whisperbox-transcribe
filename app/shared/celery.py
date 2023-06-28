from celery import Celery

from app.shared.settings import settings


def get_celery_binding() -> Celery:
    celery = Celery(
        broker_url=settings.BROKER_URL,
        broker_connection_retry=False,
        broker_connection_retry_on_startup=False,
    )
    return celery
