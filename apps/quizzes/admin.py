from django.contrib import admin
from .models import QuizRequest, Quiz, Question, Option

@admin.register(QuizRequest)
class QuizRequestAdmin(admin.ModelAdmin):
    list_display = ('topic', 'user', 'difficulty', 'question_count', 'status', 'created_at')
    list_filter = ('status', 'difficulty')
    search_fields = ('topic', 'user__username')

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'difficulty', 'is_published', 'created_at')
    list_filter = ('is_published', 'difficulty')
    search_fields = ('title', 'topic')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'body', 'order', 'points')
    list_filter = ('quiz',)
    search_fields = ('body',)

@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('question', 'body', 'is_correct', 'order')
    list_filter = ('is_correct',)
    search_fields = ('body',)
