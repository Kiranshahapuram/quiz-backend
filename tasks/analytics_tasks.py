from celery import shared_task
from services.analytics_service import AnalyticsService

@shared_task
def update_analytics_task(quiz_id):
    AnalyticsService.update_quiz_analytics(quiz_id)
