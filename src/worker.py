from celery import Celery

from src.config import settings

celery_app = Celery(
    "celery_worker",
    broker=f"redis://{settings.REDIS_SERVER}:6379/0",
    backend=f"redis://{settings.REDIS_SERVER}:6379/0"
)

celery_app.autodiscover_tasks(['src.contollers.genai.genai_controller'])
