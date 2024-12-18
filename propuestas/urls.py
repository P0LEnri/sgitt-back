from django.urls import include, path
from .views import *
from rest_framework.routers import DefaultRouter

from propuestas import views

router = DefaultRouter()
router.register(r'requisitos', RequisitoViewSet)
router.register(r'palabras-clave', PalabraClaveViewSet)
router.register(r'areas', AreaViewSet)
router.register(r'propuestas', views.PropuestaViewSet)
router.register(r'crud/propuestas', views.PropuestaViewSet, basename='crud-propuesta')
# router.register(r'crud/alumnos', views.AlumnoViewSet, basename='crud-alumno')  # Añade esta línea
# router.register(r'crud/profesores', views.ProfesorViewSet, basename='crud-profesor')  # Añade esta línea
# router.register(r'crud/propuestas/<int:pk>/', views.PropuestaDetailView, basename='crud-propuesta-admin')
# router.register(r'propuestas/<int:pk>/', views.delete_propuesta, basename='delete-propuesta')


urlpatterns = [
    path('', include(router.urls)),
    # Rutas específicas para el admin CRUD
    path('crud/propuestas/', views.PropuestaDetailView.as_view(), name='crud-propuestas-list'),
    path('crud/propuestas/<int:pk>/', views.PropuestaDetailView.as_view(), name='crud-propuesta-detail'),
    path('propuestas/<int:pk>/delete/', views.delete_propuesta, name='delete-propuesta'),
]