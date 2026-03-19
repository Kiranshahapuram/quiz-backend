from django.db import models
from core.models import BaseModel

class QuizAnalytics(BaseModel):
    quiz = models.OneToOneField('quizzes.Quiz', on_delete=models.CASCADE, related_name='analytics')
    total_attempts = models.IntegerField(default=0)
    avg_score_pct = models.FloatField(default=0.0)
    avg_completion_secs = models.IntegerField(default=0)
    question_stats = models.JSONField(default=dict)

    def __str__(self):
        return f"Analytics for {self.quiz.title}"
