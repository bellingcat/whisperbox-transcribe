from celery import Celery


def get_celery_binding(broker_url: str) -> Celery:
    return Celery(
        broker_url=broker_url,
        broker_connection_retry=False,
        broker_connection_retry_on_startup=False,
    )
