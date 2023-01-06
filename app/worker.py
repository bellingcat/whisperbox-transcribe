from celery import Celery

from .config import settings

celery = Celery(__name__)

celery.conf.broker_url = settings.REDIS_URI
