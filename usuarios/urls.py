from django.urls import path, include
from .views import *
from . import views

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register_user'),
    path('login/', LoginUserView.as_view(), name='login_user'),
    path('alumnos/', AlumnoAPI.as_view(), name='alumnos'),
    path('alumnos/perfil/', AlumnoPerfilView.as_view(), name='alumno-perfil'),
    path('profesores/', ProfesorAPI.as_view(), name='profesores'),
    path('profesores/perfil/', ProfesorPerfilView.as_view(), name='profesor-perfil'),
    path('verify-email/<uuid:token>/', VerifyEmailView.as_view(), name='verify_email'),
    path('profesores/buscar/', buscar_profesores, name='buscar_profesores'),
    path('search/', views.search_users, name='search_users'),
    path('test-data/', views.test_users_data, name='test-users-data'),
    path('materias/', views.MateriaViewSet.as_view({'get': 'list'}), name='materia-list'),
    path('materias/<int:pk>/', views.MateriaViewSet.as_view({'get': 'retrieve'}), name='materia-detail'),
    path('cambiar-contrasena-profesor/', CambiarContrasenaProfesorView.as_view(), name='cambiar-contrasena-profesor'),

]