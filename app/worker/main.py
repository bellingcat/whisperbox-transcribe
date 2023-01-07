from celery import Celery

from app.shared.config import settings

celery = Celery(__name__)

celery.conf.broker_url = settings.REDIS_URI
