from django.db import transaction
from apps.quizzes.models import Quiz, Question, Option

class QuizService:
    @staticmethod
    @transaction.atomic
    def create_quiz_from_questions(quiz_request, questions_data):
        quiz = Quiz.objects.create(
            quiz_request=quiz_request,
            title=f"Quiz on {quiz_request.topic}",
            topic=quiz_request.topic,
            difficulty=quiz_request.difficulty,
            time_limit_secs=quiz_request.question_count * 60, # 1 minute per question default
            is_published=True, # Setting published automatically upon creation for now, per usual systems.
            community=quiz_request.community
        )
        
        quiz_request.quiz = quiz
        quiz_request.status = 'completed'
        quiz_request.save()
        
        questions_to_create = []
        for i, q_data in enumerate(questions_data, start=1):
            q = Question(
                quiz=quiz,
                body=q_data['body'],
                order=i,
                points=10
            )
            questions_to_create.append((q, q_data['options']))
            
        Question.objects.bulk_create([q for q, _ in questions_to_create])
        
        # After bulk create, we must fetch questions to get their IDs
        saved_questions = list(Question.objects.filter(quiz=quiz).order_by('order'))
        
        options_to_create = []
        for q, (_, opts_data) in zip(saved_questions, questions_to_create):
            for j, opt_data in enumerate(opts_data, start=1):
                options_to_create.append(Option(
                    question=q,
                    body=opt_data['body'],
                    is_correct=opt_data['is_correct'],
                    order=j
                ))
                
        Option.objects.bulk_create(options_to_create)
        return quiz
