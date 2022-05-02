"""Celery tasks module"""

from celery import Celery
from core.config import settings
from dataclasses import dataclass


@dataclass
class Status:
    PENDING: str = "pending"
    SUCCESS: str = "success"
    ERROR: str = "error"


app = Celery(__name__)
app.conf.broker_url = settings.CELERY_BROKER_URL
app.conf.result_backend = settings.CELERY_RESULT_BACKEND
app.autodiscover_tasks()
