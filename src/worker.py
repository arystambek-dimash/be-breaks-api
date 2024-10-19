from celery import Celery, Task

celery_app = Celery(
    "celery_worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.autodiscover_tasks(['src.contollers.genai.genai_controller'])
