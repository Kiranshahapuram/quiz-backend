from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.cache import cache
from django.db.models import Sum, Count, Avg
from apps.attempts.models import Attempt
from .serializers import UserHistorySerializer

class UserMeViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def history(self, request):
        # Cursor paginated on (submitted_at DESC, id)
        # Using pagination class from settings
        attempts = Attempt.objects.filter(
            user=request.user, 
            status__in=['submitted', 'completed'],
            submitted_at__isnull=False
        ).select_related('quiz').order_by('-submitted_at', '-id')
        
        paginator = self.pagination_class() if hasattr(self, 'pagination_class') else None
        if paginator is None:
            # Fallback to DRF defaults if generic viewset doesn't auto-attach it in viewset base
            from rest_framework.settings import api_settings
            paginator = api_settings.DEFAULT_PAGINATION_CLASS()
        
        paginator.ordering = '-submitted_at'
            
        page = paginator.paginate_queryset(attempts, request, view=self)
        if page is not None:
            serializer = UserHistorySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
            
        serializer = UserHistorySerializer(attempts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def performance(self, request):
        user_id = request.user.id
        cache_key = f"user:{user_id}:performance"
        
        data = cache.get(cache_key)
        if data:
            return Response(data)
            
        attempts = Attempt.objects.filter(user_id=user_id, status__in=['submitted', 'completed'])
        
        total_attempts = attempts.count()
        if total_attempts == 0:
            data = {"total_attempts": 0, "avg_score_pct": 0, "by_topic": [], "by_difficulty": [], "best_topic": None, "weakest_topic": None}
            cache.set(cache_key, data, 300)
            return Response(data)
            
        # Compute overall avg
        sum_score = attempts.aggregate(s=Sum('score'))['s'] or 0
        sum_max = attempts.aggregate(s=Sum('max_score'))['s'] or 1
        avg_score_pct = round((sum_score / sum_max) * 100, 2)
        
        # By topic
        topics = {}
        for att in attempts.select_related('quiz'):
            topic = att.quiz.topic
            if topic not in topics:
                topics[topic] = {'score': 0, 'max_score': 0, 'count': 0}
            topics[topic]['score'] += att.score
            topics[topic]['max_score'] += att.max_score
            topics[topic]['count'] += 1
            
        by_topic = []
        for topic, stat in topics.items():
            pct = round((stat['score'] / stat['max_score']) * 100, 2) if stat['max_score'] else 0
            by_topic.append({
                "topic": topic,
                "total_attempts": stat['count'],
                "avg_score_pct": pct
            })
            
        # Best / Weakest
        ordered_topics = sorted(by_topic, key=lambda x: x['avg_score_pct'])
        best_topic = ordered_topics[-1]['topic'] if ordered_topics else None
        weakest_topic = ordered_topics[0]['topic'] if ordered_topics else None
        
        # By difficulty
        diffs = {}
        for att in attempts.select_related('quiz'):
            diff = att.quiz.difficulty
            if diff not in diffs:
                diffs[diff] = {'score': 0, 'max_score': 0, 'count': 0}
            diffs[diff]['score'] += att.score
            diffs[diff]['max_score'] += att.max_score
            diffs[diff]['count'] += 1
            
        by_difficulty = []
        for diff, stat in diffs.items():
            pct = round((stat['score'] / stat['max_score']) * 100, 2) if stat['max_score'] else 0
            by_difficulty.append({
                "difficulty": diff,
                "total_attempts": stat['count'],
                "avg_score_pct": pct
            })
            
        data = {
            "total_attempts": total_attempts,
            "avg_score_pct": avg_score_pct,
            "by_topic": by_topic,
            "by_difficulty": by_difficulty,
            "best_topic": best_topic,
            "weakest_topic": weakest_topic
        }
        
        cache.set(cache_key, data, 300) # 5m cache
        return Response(data)
