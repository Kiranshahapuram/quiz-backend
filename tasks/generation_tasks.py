from celery import shared_task
from apps.quizzes.models import QuizRequest
from services.ai_service import AIService, AIServiceError, AIRateLimitError
from services.quiz_service import QuizService

@shared_task(bind=True, max_retries=3, autoretry_for=(AIServiceError,), retry_backoff=True)
def generate_quiz_task(self, quiz_request_id):
    try:
        quiz_request = QuizRequest.objects.get(id=quiz_request_id)
    except QuizRequest.DoesNotExist:
        return
        
    if quiz_request.status != 'pending':
        return
        
    quiz_request.status = 'processing'
    quiz_request.save()
    
    try:
        questions_data = AIService.generate_questions(
            topic=quiz_request.topic,
            difficulty=quiz_request.difficulty,
            count=quiz_request.question_count
        )
        QuizService.create_quiz_from_questions(quiz_request, questions_data)
    except AIRateLimitError as exc:
        quiz_request.status = 'pending'
        quiz_request.save()
        raise self.retry(exc=exc, countdown=120)
    except Exception as exc:
        quiz_request.status = 'failed'
        quiz_request.failure_reason = str(exc)
        quiz_request.save()
        raise AIServiceError(str(exc)) # re-raising for autoretry_for (it will bump retries until max and then stop)
