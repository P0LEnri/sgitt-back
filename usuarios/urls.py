from django.urls import include, path
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'alumnos', views.AlumnoViewSet)
router.register(r'profesores', views.ProfesorViewSet)


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
    path('crud/alumnos/', views.AlumnoListCreateView.as_view(), name='crud-alumnos-list'),
    path('crud/alumnos/<int:pk>/', views.AlumnoDetailView.as_view(), name='crud-alumno-detail'),
    path('alumnos/<int:pk>/delete/', views.delete_alumno, name='delete-alumno'),

    # Profesores
    path('profesores/', views.ProfesorAPI.as_view(), name='profesores-list'),
    path('profesores/perfil/', views.ProfesorPerfilView.as_view(), name='profesor-perfil'),
    path('profesores/buscar/', views.buscar_profesores, name='buscar-profesores'),
    path('crud/profesores/', views.ProfesorListCreateView.as_view(), name='crud-profesores-list'),
    path('crud/profesores/<int:pk>/', views.ProfesorDetailView.as_view(), name='crud-profesor-detail'),
    path('profesores/<int:pk>/delete/', views.delete_profesor, name='delete-profesor'),
    
    # Materias
    path('materias/', views.MateriaViewSet.as_view({'get': 'list'}), name='materia-list'),
    path('materias/<int:pk>/', views.MateriaViewSet.as_view({'get': 'retrieve'}), name='materia-detail'),
    path('check-admin/', views.check_admin, name='check-admin'),
    path('', include(router.urls)),
    path('reset-password-request/', views.ResetPasswordRequestView.as_view(), name='reset-password-request'),
    path('reset-password/<uuid:token>/', views.ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),
    path('cambiar-contrasena/', views.CambiarContrasenaView.as_view(), name='cambiar-contrasena'),
    path('alumno/buscar/', views.buscar_alumnos, name='buscar_alumnos'),

    # Reportes
    path('reports/problem/', views.report_problem, name='report_problem'),
 

]
