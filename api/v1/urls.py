from django.urls import path, include

urlpatterns = [
    path('auth/', include('api.v1.auth.urls')),
    path('users/', include('api.v1.users.urls')),
    path('quizzes/', include('api.v1.quizzes.urls')),
    path('attempts/', include('api.v1.attempts.urls')),
    path('communities/', include('api.v1.communities.urls')),
    path('admin/', include('api.v1.admin.urls')),
]
