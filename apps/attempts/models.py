from django.db import models
from core.models import BaseModel

class Attempt(BaseModel):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='attempts')
    quiz = models.ForeignKey('quizzes.Quiz', on_delete=models.CASCADE, related_name='attempts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    score = models.IntegerField(default=0)
    max_score = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'quiz')

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} ({self.status})"

class AttemptAnswer(BaseModel):
    attempt = models.ForeignKey('Attempt', on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey('quizzes.Question', on_delete=models.CASCADE)
    selected_option = models.ForeignKey('quizzes.Option', on_delete=models.SET_NULL, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    points_awarded = models.IntegerField(default=0)
    answered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Answer to {self.question.id} by {self.attempt.user.username}"
