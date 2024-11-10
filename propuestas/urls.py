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
    # path('propuestas/', views.PropuestaViewSet.as_view({'get': 'list', 'post': 'create'}), name='propuestas-list'),
    # path('propuestas/<int:pk>/', views.PropuestaViewSet.as_view({
    #     'get': 'retrieve',
    #     'put': 'update',
    #     'patch': 'partial_update',
    #     'delete': 'destroy'
    # }), name='propuesta-detail'),
    # Para el detail view, usar path normal
    path('crud/propuestas/<int:pk>/', views.PropuestaDetailView.as_view(), name='crud-propuesta-detail'),
    # path('crud/alumnos/<int:pk>/', views.AlumnoDetailView.as_view(), name='crud-alumno-detail'),
    # path('crud/profesores/<int:pk>/', views.ProfesorDetailView.as_view(), name='crud-profesor-detail'),
    # Para el delete, usar path normal
    path('propuestas/<int:pk>/delete/', views.delete_propuesta, name='delete-propuesta'),
    
]
