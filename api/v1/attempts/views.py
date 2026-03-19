from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db import IntegrityError
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .serializers import AttemptResultSerializer, AttemptAnswerPatchSerializer
from apps.attempts.models import Attempt, AttemptAnswer
from apps.quizzes.models import Quiz, Question, Option
from services.attempt_service import AttemptService
from tasks.analytics_tasks import update_analytics_task
from api.exceptions import CustomAPIException
from api.permissions import IsOwnerOrAdmin

class AttemptViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    queryset = Attempt.objects.all()

    def get_serializer_class(self):
        return AttemptResultSerializer

    def create(self, request, *args, **kwargs):
        quiz_id = request.data.get('quiz_id')
        if not quiz_id:
            raise CustomAPIException("quiz_id is required", code="VALIDATION_ERROR", field="quiz_id", status_code=400)
            
        quiz = get_object_or_404(Quiz, id=quiz_id)
        if not quiz.is_published:
            raise CustomAPIException("This quiz is not published.", code="QUIZ_NOT_PUBLISHED", status_code=403)
        
        # Verify access: user must be a community member or own the personal quiz
        if quiz.community:
            if not quiz.community.members.filter(id=request.user.id).exists():
                raise CustomAPIException("You are not a member of this quiz's community.", code="PERMISSION_DENIED", status_code=403)
        else:
            # Personal quiz — only the creator can attempt
            if hasattr(quiz, 'quiz_request') and quiz.quiz_request.user != request.user:
                raise CustomAPIException("This is a private quiz.", code="PERMISSION_DENIED", status_code=403)
            
        try:
            attempt = Attempt.objects.create(user=request.user, quiz=quiz)
        except IntegrityError:
            raise CustomAPIException("An attempt for this quiz already exists.", code="DUPLICATE_ATTEMPT", status_code=409)
            
        return Response(AttemptResultSerializer(attempt).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='answer')
    def answer(self, request, pk=None):
        attempt = self.get_object()
        
        if attempt.status != 'in_progress':
            raise CustomAPIException("Cannot submit answers to a completed attempt.", code="ATTEMPT_SUBMITTED", status_code=403)
            
        serializer = AttemptAnswerPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        q_id = serializer.validated_data['question_id']
        opt_id = serializer.validated_data['option_id']
        
        question = get_object_or_404(Question, id=q_id)
        if question.quiz_id != attempt.quiz_id:
            raise CustomAPIException("Question does not belong to this quiz.", code="VALIDATION_ERROR", field="question_id", status_code=400)
            
        option = get_object_or_404(Option, id=opt_id)
        if option.question_id != question.id:
            raise CustomAPIException("Option does not belong to this question.", code="VALIDATION_ERROR", field="option_id", status_code=400)
            
        answer, created = AttemptAnswer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={
                'selected_option': option,
                'answered_at': timezone.now()
            }
        )
        
        return Response({
            "message": "Answer recorded.",
            "answered_at": answer.answered_at
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        attempt = self.get_object()
        
        # Make sure that checking works even when using the wrong action name.
        if attempt.status != 'in_progress':
            raise CustomAPIException("Attempt has already been submitted.", code="ATTEMPT_SUBMITTED", status_code=403)
            
        scored_attempt = AttemptService.score_attempt(attempt)
        update_analytics_task.delay(str(scored_attempt.quiz_id))
        
        return Response(AttemptResultSerializer(scored_attempt).data, status=status.HTTP_200_OK)
