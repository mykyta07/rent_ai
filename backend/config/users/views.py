from rest_framework import generics, status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter

from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer
)

User = get_user_model()


@extend_schema(
    tags=['Authentication'],
    summary='Реєстрація користувача',
    description='Створення нового користувача з автоматичною генерацією JWT токенів',
    examples=[
        OpenApiExample(
            'Register Example',
            value={
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePassword123",
                "password_confirm": "SecurePassword123",
                "first_name": "John",
                "last_name": "Doe"
            }
        )
    ],
    auth=[]  # ← Вимикає авторизацію для цього endpoint
)
class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    
    Реєстрація нового користувача
    
    Body:
    {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecurePassword123",
        "password_confirm": "SecurePassword123",
        "first_name": "John",
        "last_name": "Doe"
    }
    
    Response:
    {
        "user": {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "role": "buyer"
        },
        "tokens": {
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
        }
    }
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Генеруємо JWT токени для нового користувача
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Authentication'],
    summary='Вхід користувача',
    description='Отримання JWT токенів для авторизації',
    auth=[]  # ← Вимикає авторизацію
)
class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    
    Вхід користувача (отримання JWT токенів)
    
    Body:
    {
        "username": "john_doe",
        "password": "SecurePassword123"
    }
    
    Response:
    {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
    """
    permission_classes = (AllowAny,)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    
    Вихід користувача (додавання refresh token в blacklist)
    
    Body:
    {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
    """
    permission_classes = (IsAuthenticated,)
    
    class InputSerializer(serializers.Serializer):
        refresh = serializers.CharField()
    
    serializer_class = InputSerializer
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {"message": "Успішно вийшли з системи"},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/auth/profile/
    Отримання профілю поточного користувача
    
    PUT/PATCH /api/auth/profile/
    Оновлення профілю
    
    Body (для PUT/PATCH):
    {
        "first_name": "John",
        "last_name": "Doe",
        "email": "newemail@example.com"
    }
    """
    permission_classes = (IsAuthenticated,)
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        return UserUpdateSerializer


class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/
    
    Зміна паролю користувача
    
    Body:
    {
        "old_password": "OldPassword123",
        "new_password": "NewPassword123",
        "new_password_confirm": "NewPassword123"
    }
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = ChangePasswordSerializer
    
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Змінюємо пароль
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            
            return Response(
                {"message": "Пароль успішно змінено"},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):
    """
    GET /api/users/
    
    Список всіх користувачів (тільки для адміністраторів)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self):
        # Тільки адміни можуть бачити всіх користувачів
        if self.request.user.is_staff:
            return User.objects.all()
        # Звичайні користувачі бачать тільки себе
        return User.objects.filter(id=self.request.user.id)
