from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from django.core.cache import cache
from django.utils import timezone
from api.permissions import IsAdminRole
from apps.quizzes.models import Quiz
from .serializers import AdminQuizSerializer, AdminQuizUpdateSerializer

class AdminQuizViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminRole]
    queryset = Quiz.objects.all().order_by('-created_at')
    ordering = ['-created_at', '-id']

    def get_serializer_class(self):
        if self.action in ['partial_update', 'update']:
            return AdminQuizUpdateSerializer
        return AdminQuizSerializer

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
        
    def partial_update(self, request, *args, **kwargs):
        res = super().partial_update(request, *args, **kwargs)
        # Invalidate quiz cache on edit
        quiz = self.get_object()
        cache.delete(f"quiz:{quiz.id}:detail")
        quiz.quiz_request.status = 'completed' if quiz.is_published else 'pending'
        return res

    def destroy(self, request, *args, **kwargs):
        # Soft delete
        quiz = self.get_object()
        quiz.deleted_at = timezone.now()
        quiz.is_published = False
        quiz.save()
        cache.delete(f"quiz:{quiz.id}:detail")
        return Response(status=status.HTTP_204_NO_CONTENT)
