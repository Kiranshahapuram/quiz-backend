from django.db.models import Avg, Count, F, ExpressionWrapper, FloatField, Sum
from django.core.cache import cache
from apps.attempts.models import Attempt, AttemptAnswer
from apps.analytics.models import QuizAnalytics
from apps.quizzes.models import Quiz

class AnalyticsService:
    @staticmethod
    def update_quiz_analytics(quiz_id):
        # Only aggregate submitted/completed attempts
        attempts = Attempt.objects.filter(quiz_id=quiz_id, status__in=['submitted', 'completed'])
        
        total_attempts = attempts.count()
        if total_attempts == 0:
            return
            
        # Calculate averages using python for simplicity and accuracy over full set, 
        # or Django aggregation
        agg = attempts.aggregate(
            total=Count('id'),
            sum_score=Sum('score'),
            sum_max_score=Sum('max_score')
        )
        
        sum_score = agg['sum_score'] or 0
        sum_max_score = agg['sum_max_score'] or 1 # avoid div by zero
        avg_score_pct = (sum_score / sum_max_score) * 100 if sum_max_score > 0 else 0.0
        
        # Calculate avg_completion_secs from started_at and submitted_at
        total_secs = 0
        valid_time_attempts = 0
        for att in attempts:
            if att.submitted_at and att.started_at:
                total_secs += (att.submitted_at - att.started_at).total_seconds()
                valid_time_attempts += 1
                
        avg_completion_secs = int(total_secs / valid_time_attempts) if valid_time_attempts > 0 else 0
        
        # Calculate per question stats
        question_stats = {}
        answers = AttemptAnswer.objects.filter(attempt__in=attempts).select_related('question')
        
        q_data = {}
        for ans in answers:
            qid = str(ans.question.id)
            if qid not in q_data:
                q_data[qid] = {'correct': 0, 'total': 0, 'times': []}
                
            q_data[qid]['total'] += 1
            if ans.is_correct:
                q_data[qid]['correct'] += 1
            if ans.answered_at and ans.attempt.started_at:
                q_data[qid]['times'].append((ans.answered_at - ans.attempt.started_at).total_seconds())

        for qid, stat in q_data.items():
            correct_rate = (stat['correct'] / stat['total']) * 100 if stat['total'] > 0 else 0
            avg_time = sum(stat['times']) / len(stat['times']) if stat['times'] else 0
            question_stats[qid] = {
                'correct_rate_pct': round(correct_rate, 2),
                'avg_time_secs': int(avg_time)
            }
            
        analytics, _ = QuizAnalytics.objects.update_or_create(
            quiz_id=quiz_id,
            defaults={
                'total_attempts': total_attempts,
                'avg_score_pct': round(avg_score_pct, 2),
                'avg_completion_secs': avg_completion_secs,
                'question_stats': question_stats
            }
        )
        
        # Invalidate related caches
        cache.delete(f"quiz:{quiz_id}:analytics")
        
        # We should also invalidate performance caches for all users who took this quiz,
        # but to keep it simple we invalidate the users in this batch.
        for att in attempts.select_related('user').distinct():
            cache.delete(f"user:{att.user.id}:performance")
            
        return analytics
