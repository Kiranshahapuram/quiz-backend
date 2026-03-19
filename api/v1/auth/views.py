from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from .serializers import RegisterSerializer, UserSerializer
from api.exceptions import CustomAPIException

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
        except InvalidToken as e:
            raise CustomAPIException('Invalid credentials.', code='INVALID_CREDENTIALS', status_code=401)
            
        # Instead of just returning tokens, we return user info + tokens
        # We need to get the user from the email/password
        from apps.users.models import User
        email = request.data.get('email')
        
        try:
            user = User.objects.get(email=email)
            data = response.data
            data['user'] = UserSerializer(user).data
            return Response(data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            raise CustomAPIException('Invalid credentials.', code='INVALID_CREDENTIALS', status_code=401)

class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                raise CustomAPIException("Refresh token is required.", code="VALIDATION_ERROR", field="refresh", status_code=400)
                
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            raise CustomAPIException("Token is invalid or expired.", code="TOKEN_INVALID", status_code=401)
