from django.utils import timezone
from apps.attempts.models import Attempt, AttemptAnswer
from apps.quizzes.models import Question

class AttemptService:
    @staticmethod
    def score_attempt(attempt):
        # We must score against ALL questions in the quiz, not just the ones answered.
        all_questions = list(Question.objects.filter(quiz=attempt.quiz).prefetch_related('options'))
        
        # Get existing answers
        existing_answers = {str(a.question_id): a for a in AttemptAnswer.objects.filter(attempt=attempt)}
        
        total_score = 0
        max_score = 0
        
        answers_to_update = []
        answers_to_create = []

        for q in all_questions:
            # Add to max score
            max_score += q.points
            
            # Check if user answered
            ans = existing_answers.get(str(q.id))
            correct_option = next((o for o in q.options.all() if o.is_correct), None)
            
            if ans:
                # User answered
                if ans.selected_option_id and correct_option and ans.selected_option_id == correct_option.id:
                    ans.is_correct = True
                    ans.points_awarded = q.points
                    total_score += q.points
                else:
                    ans.is_correct = False
                    ans.points_awarded = 0
                answers_to_update.append(ans)
            else:
                # Question skipped - create a "ghost" wrong answer record for history and analytics
                ans = AttemptAnswer(
                    attempt=attempt,
                    question=q,
                    is_correct=False,
                    points_awarded=0,
                    answered_at=timezone.now()
                )
                answers_to_create.append(ans)

        # Batch persist
        if answers_to_update:
            AttemptAnswer.objects.bulk_update(answers_to_update, ['is_correct', 'points_awarded'])
        if answers_to_create:
            AttemptAnswer.objects.bulk_create(answers_to_create)
            
        # Complete attempt
        attempt.status = 'submitted'
        attempt.score = total_score
        attempt.max_score = max_score
        attempt.submitted_at = timezone.now()
        attempt.save(update_fields=['status', 'score', 'max_score', 'submitted_at'])
        
        return attempt
