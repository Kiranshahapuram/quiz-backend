from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminQuizViewSet

router = DefaultRouter()
router.register(r'quizzes', AdminQuizViewSet, basename='admin-quiz')

urlpatterns = [
    path('', include(router.urls)),
]
