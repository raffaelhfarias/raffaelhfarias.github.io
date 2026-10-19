from celery import Celery

from .config import settings

celery_app = Celery(
    "enterprise_knowledge_ai", broker=settings().redis_url, backend=settings().redis_url
)
