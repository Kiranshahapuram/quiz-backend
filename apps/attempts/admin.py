from django.contrib import admin
from .models import Attempt, AttemptAnswer

@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'status', 'score', 'max_score', 'started_at')
    list_filter = ('status',)
    search_fields = ('user__username', 'quiz__title')

@admin.register(AttemptAnswer)
class AttemptAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'is_correct', 'points_awarded')
    list_filter = ('is_correct',)
