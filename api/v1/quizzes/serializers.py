from rest_framework import serializers
from apps.quizzes.models import QuizRequest, Quiz, Question, Option

class QuizRequestReadSerializer(serializers.ModelSerializer):
    quiz_id = serializers.UUIDField(source='quiz.id', read_only=True)

    class Meta:
        model = QuizRequest
        fields = ('id', 'topic', 'difficulty', 'question_count', 'status', 'failure_reason', 'quiz_id', 'created_at')

class QuizRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizRequest
        fields = ('topic', 'difficulty', 'question_count')

    def create(self, validated_data):
        user = self.context['request'].user
        return QuizRequest.objects.create(user=user, **validated_data)

class PublicOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ('id', 'body', 'order')
        # CRITICAL: NO is_correct

class PublicQuestionSerializer(serializers.ModelSerializer):
    options = PublicOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ('id', 'body', 'question_type', 'order', 'points', 'options')

class PublicQuizSerializer(serializers.ModelSerializer):
    questions = PublicQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ('id', 'title', 'topic', 'difficulty', 'time_limit_secs', 'questions')

class QuizListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ('id', 'title', 'topic', 'difficulty', 'time_limit_secs', 'created_at')
