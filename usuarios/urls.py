from django.urls import path
from . import views

urlpatterns = [
    # Autenticación y Registro
    path('register/', views.RegisterUserView.as_view(), name='register_user'),
    path('login/', views.LoginUserView.as_view(), name='login_user'),
    path('verify-email/<uuid:token>/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('cambiar-contrasena-profesor/', views.CambiarContrasenaProfesorView.as_view(), name='cambiar-contrasena-profesor'),
    
    # Usuarios (Búsqueda y Datos de Prueba)
    path('search/', views.search_users, name='search_users'),
    path('test-data/', views.test_users_data, name='test-users-data'),

    # Alumnos
    path('alumnos/', views.AlumnoAPI.as_view(), name='alumnos-list'),
    path('alumnos/perfil/', views.AlumnoPerfilView.as_view(), name='alumno-perfil'),
    path('alumnos/<int:pk>/', views.AlumnoDetailView.as_view(), name='alumno-detail'),
    path('crud/alumnos/', views.AlumnoListView.as_view(), name='crud-alumnos-list'),
    path('crud/alumnos/<int:pk>/', views.AlumnoDetailView.as_view(), name='crud-alumno-detail'),
    path('alumnos/<int:pk>/delete/', views.delete_alumno, name='delete-alumno'),

    # Profesores (Perfil, CRUD y Búsqueda)
    path('profesores/', views.ProfesorAPI.as_view(), name='profesores-list'),
    path('profesores/perfil/', views.ProfesorPerfilView.as_view(), name='profesor-perfil'),
    path('profesores/buscar/', views.buscar_profesores, name='buscar-profesores'),
    path('crud/profesores/', views.ProfesorListView.as_view(), name='crud-profesores-list'),
    path('crud/profesores/<int:pk>/', views.ProfesorDetailView.as_view(), name='crud-profesor-detail'),
    path('profesores/<int:pk>/delete/', views.delete_profesor, name='delete-profesor'),

    # Materias
    path('materias/', views.MateriaViewSet.as_view({'get': 'list'}), name='materia-list'),
    path('materias/<int:pk>/', views.MateriaViewSet.as_view({'get': 'retrieve'}), name='materia-detail'),
]
