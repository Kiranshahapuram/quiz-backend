from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserMeViewSet

router = DefaultRouter()
router.register(r'me', UserMeViewSet, basename='user-me')

urlpatterns = [
    path('', include(router.urls)),
]
