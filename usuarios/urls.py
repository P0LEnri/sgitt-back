from django.urls import path, include
from .views import *

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register_user'),
    path('login/', LoginUserView.as_view(), name='login_user'),
    path('alumnos/', AlumnoAPI.as_view(), name='alumnos'),
    path('profesores/', ProfesorAPI.as_view(), name='profesores'),
    path('verify-email/<uuid:token>/', VerifyEmailView.as_view(), name='verify_email'),
    path('profesores/buscar/', buscar_profesores, name='buscar_profesores'),
]