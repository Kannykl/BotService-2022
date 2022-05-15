"""Celery tasks module"""

from celery import Celery
from core.config import settings


app = Celery(__name__, include=["services.vk.bots_creation.tasks", "services.vk.stat_boost.tasks"])
app.conf.broker_url = settings.CELERY_BROKER_URL
app.conf.result_backend = settings.CELERY_RESULT_BACKEND
app.autodiscover_tasks()
