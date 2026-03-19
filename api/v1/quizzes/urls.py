from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QuizRequestViewSet, QuizViewSet

router = DefaultRouter()
router.register(r'quiz-requests', QuizRequestViewSet, basename='quiz-request')
router.register(r'', QuizViewSet, basename='quiz')

urlpatterns = [
    # Include the router urls
    path('', include(router.urls)),
]
