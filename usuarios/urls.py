from django.urls import path, include
from .views import *

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register_user'),
    path('login/', LoginUserView.as_view(), name='login_user'),
    path('verify-email/<uuid:token>/', VerifyEmailView.as_view(), name='verify_email'),
]