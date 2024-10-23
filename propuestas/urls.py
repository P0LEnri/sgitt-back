from django.urls import include, path
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'requisitos', RequisitoViewSet)
router.register(r'palabras-clave', PalabraClaveViewSet)
router.register(r'areas', AreaViewSet)
router.register(r'propuestas', PropuestaViewSet)

urlpatterns = [
    path('', include(router.urls))
]
