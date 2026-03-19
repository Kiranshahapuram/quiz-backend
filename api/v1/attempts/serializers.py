from rest_framework import serializers
from apps.attempts.models import Attempt, AttemptAnswer
from apps.quizzes.models import Quiz, Question, Option

class AttemptAnswerPatchSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    option_id = serializers.UUIDField()

class AttemptAnswerResultSerializer(serializers.ModelSerializer):
    question_body = serializers.CharField(source='question.body', read_only=True)
    selected_option_body = serializers.SerializerMethodField()
    correct_option_id = serializers.SerializerMethodField()
    correct_option_body = serializers.SerializerMethodField()

    class Meta:
        model = AttemptAnswer
        fields = (
            'id', 'question_id', 'question_body', 'selected_option_id', 
            'selected_option_body', 'correct_option_id', 'correct_option_body', 
            'is_correct', 'points_awarded'
        )
        
    def get_selected_option_body(self, obj):
        if obj.selected_option:
            return obj.selected_option.body
        return None
        
    def get_correct_option_id(self, obj):
        opt = obj.question.options.filter(is_correct=True).first()
        return opt.id if opt else None
        
    def get_correct_option_body(self, obj):
        opt = obj.question.options.filter(is_correct=True).first()
        return opt.body if opt else None

class AttemptResultSerializer(serializers.ModelSerializer):
    answers = serializers.SerializerMethodField()
    score_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Attempt
        fields = ('id', 'quiz_id', 'status', 'score', 'max_score', 'score_percentage', 'started_at', 'submitted_at', 'answers')
        
    def get_answers(self, obj):
        # We enforce logic: If in progress, omit is_correct-related fields.
        if obj.status == 'in_progress':
            qs = obj.answers.all()
            return [
                {
                    "question_id": a.question_id,
                    "selected_option_id": a.selected_option_id,
                    "answered_at": a.answered_at
                } for a in qs
            ]
        # Return full breakdown if completed
        return AttemptAnswerResultSerializer(obj.answers.all(), many=True).data

    def get_score_percentage(self, obj):
        if obj.max_score > 0:
            return round((obj.score / obj.max_score) * 100, 2)
        return 0.0
