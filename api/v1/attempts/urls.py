from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AttemptViewSet

router = DefaultRouter()
router.register(r'', AttemptViewSet, basename='attempt')

urlpatterns = [
    path('', include(router.urls)),
]
