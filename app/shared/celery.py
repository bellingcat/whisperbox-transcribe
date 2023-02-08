from celery import Celery

from app.shared.settings import settings


def get_celery_binding() -> Celery:
    celery = Celery()
    celery.conf.broker_url = settings.BROKER_URL
    return celery
