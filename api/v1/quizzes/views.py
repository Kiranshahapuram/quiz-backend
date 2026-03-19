from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from .serializers import (
    QuizRequestCreateSerializer, QuizRequestReadSerializer,
    PublicQuizSerializer, QuizListSerializer
)
from apps.quizzes.models import QuizRequest, Quiz
from apps.analytics.models import QuizAnalytics
from tasks.generation_tasks import generate_quiz_task
from api.exceptions import CustomAPIException

class QuizRequestViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return QuizRequestCreateSerializer
        return QuizRequestReadSerializer

    def get_queryset(self):
        return QuizRequest.objects.filter(user=self.request.user).order_by('-created_at', 'id')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quiz_request = serializer.save()
        
        # Dispatch celery task
        generate_quiz_task.delay(str(quiz_request.id))
        
        read_serializer = QuizRequestReadSerializer(quiz_request)
        return Response(read_serializer.data, status=status.HTTP_202_ACCEPTED)

class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    filterset_fields = ['topic', 'difficulty']

    def get_serializer_class(self):
        if self.action == 'list':
            return QuizListSerializer
        return PublicQuizSerializer

    def get_queryset(self):
        qs = Quiz.objects.filter(is_published=True, deleted_at__isnull=True).order_by('-created_at', 'id')
        if self.action == 'retrieve':
            qs = qs.prefetch_related('questions__options')
        return qs

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        cache_key = f"quiz:{instance.id}:detail"
        
        data = cache.get(cache_key)
        if data:
            return Response(data)
            
        serializer = self.get_serializer(instance)
        data = serializer.data
        cache.set(cache_key, data, timeout=3600)  # 1h TTL
        return Response(data)

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        quiz = self.get_object()
        
        # Accessible to creator + admins
        is_creator = False
        if getattr(quiz, 'quiz_request', None) and getattr(quiz.quiz_request, 'user', None) == request.user:
            is_creator = True
            
        if not (is_creator or request.user.role == 'admin'):
            raise CustomAPIException("Permission denied.", code="PERMISSION_DENIED", status_code=403)
            
        cache_key = f"quiz:{quiz.id}:analytics"
        data = cache.get(cache_key)
        if data:
            return Response(data)
            
        analytics_obj = get_object_or_404(QuizAnalytics, quiz=quiz)
        
        data = {
            "total_attempts": analytics_obj.total_attempts,
            "avg_score_pct": analytics_obj.avg_score_pct,
            "avg_completion_secs": analytics_obj.avg_completion_secs,
            "question_stats": analytics_obj.question_stats
        }
        cache.set(cache_key, data, timeout=900)  # 15 min TTL
        return Response(data)
