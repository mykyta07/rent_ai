from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserProfileView,
    ChangePasswordView,
    UserListView
)

urlpatterns = [
    # Автентифікація
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Профіль користувача
    path('auth/profile/', UserProfileView.as_view(), name='user-profile'),
    path('users/me/', UserProfileView.as_view(), name='user-me'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # Список користувачів
    path('users/', UserListView.as_view(), name='user-list'),
]
