from rest_framework import serializers
from apps.quizzes.models import Quiz
from apps.users.models import User

class AdminQuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ('id', 'title', 'topic', 'difficulty', 'is_published', 'deleted_at', 'created_at')

class AdminQuizUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ('is_published',)
