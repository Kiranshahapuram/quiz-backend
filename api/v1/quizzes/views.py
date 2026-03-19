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
        from django.db.models import Q
        user = self.request.user
        
        # Base filters: published and not deleted
        qs = Quiz.objects.filter(is_published=True, deleted_at__isnull=True)
        
        # Access logic: 
        # 1. Member of the community the quiz belongs to
        # 2. Or it's a personal quiz (no community) created by the user
        user_communities = user.communities.all()
        
        qs = qs.filter(
            Q(community__in=user_communities) |
            (Q(community__isnull=True) & Q(quiz_request__user=user))
        ).distinct()

        # Optional: filter by specific community via query param
        community_id = self.request.query_params.get('community')
        if community_id == 'personal':
            qs = qs.filter(community__isnull=True)
        elif community_id:
            qs = qs.filter(community_id=community_id)

        qs = qs.order_by('-created_at', 'id')
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
        
        # Accessible to: creator, admins, or any member of the quiz's community
        is_creator = False
        if getattr(quiz, 'quiz_request', None) and getattr(quiz.quiz_request, 'user', None) == request.user:
            is_creator = True
        
        is_community_member = False
        if quiz.community and quiz.community.members.filter(id=request.user.id).exists():
            is_community_member = True
            
        if not (is_creator or is_community_member or request.user.role == 'admin'):
            raise CustomAPIException("Permission denied.", code="PERMISSION_DENIED", status_code=403)
            
        cache_key = f"quiz:{quiz.id}:analytics"
        data = cache.get(cache_key)
        if data:
            return Response(data)
            
        analytics_obj, _ = QuizAnalytics.objects.get_or_create(quiz=quiz)
        
        data = {
            "total_attempts": analytics_obj.total_attempts,
            "avg_score_pct": analytics_obj.avg_score_pct,
            "avg_completion_secs": analytics_obj.avg_completion_secs,
            "question_stats": analytics_obj.question_stats
        }
        cache.set(cache_key, data, timeout=900)  # 15 min TTL
        return Response(data)
