from rest_framework import serializers
from apps.attempts.models import Attempt

class UserHistorySerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    topic = serializers.CharField(source='quiz.topic', read_only=True)
    difficulty = serializers.CharField(source='quiz.difficulty', read_only=True)
    score_percentage = serializers.SerializerMethodField()
    quiz_topic = serializers.CharField(source='quiz.topic', read_only=True)

    class Meta:
        model = Attempt
        fields = ('id', 'quiz_id', 'quiz_title', 'quiz_topic', 'topic', 'difficulty', 'score', 'max_score', 'score_percentage', 'submitted_at')

    def get_score_percentage(self, obj):
        if obj.max_score > 0:
            return round((obj.score / obj.max_score) * 100, 2)
        return 0.0
