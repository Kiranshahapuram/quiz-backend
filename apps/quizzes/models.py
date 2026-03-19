from django.db import models
from core.models import BaseModel

class QuizRequest(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='quiz_requests')
    topic = models.CharField(max_length=255)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    question_count = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    failure_reason = models.TextField(null=True, blank=True)
    quiz = models.OneToOneField('Quiz', on_delete=models.SET_NULL, null=True, blank=True, related_name='request_source')

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=['pending', 'processing', 'completed', 'failed']),
                name='quizrequest_status_check'
            ),
            models.CheckConstraint(
                condition=models.Q(question_count__gte=1, question_count__lte=50),
                name='quizrequest_question_count_check'
            )
        ]

    def __str__(self):
        return f"{self.topic} ({self.status})"

class Quiz(BaseModel):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    quiz_request = models.OneToOneField('QuizRequest', on_delete=models.CASCADE, related_name='generated_quiz')
    title = models.CharField(max_length=255)
    topic = models.CharField(max_length=255)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    time_limit_secs = models.IntegerField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

class Question(BaseModel):
    quiz = models.ForeignKey('Quiz', on_delete=models.CASCADE, related_name='questions')
    body = models.TextField()
    question_type = models.CharField(max_length=50, default='multiple_choice')
    order = models.IntegerField()
    points = models.IntegerField(default=10)

    def __str__(self):
        return f"Q{self.order}: {self.body[:50]}"

class Option(BaseModel):
    question = models.ForeignKey('Question', on_delete=models.CASCADE, related_name='options')
    body = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['question'],
                condition=models.Q(is_correct=True),
                name='unique_correct_option_per_question'
            )
        ]

    def __str__(self):
        return self.body
