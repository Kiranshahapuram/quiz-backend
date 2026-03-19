from django.contrib import admin
from .models import QuizAnalytics

@admin.register(QuizAnalytics)
class QuizAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'total_attempts', 'avg_score_pct', 'avg_completion_secs')
    search_fields = ('quiz__title',)
