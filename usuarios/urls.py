from django.urls import path, include
from .views import *

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register_user'),
    path('login/', LoginUserView.as_view(), name='login_user'),
    path('alumnos/', AlumnoAPI.as_view(), name='alumnos'),
    path('profesores/', ProfesorAPI.as_view(), name='profesores'),
]