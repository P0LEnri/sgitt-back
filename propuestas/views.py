from rest_framework import viewsets, permissions
from django.core.exceptions import PermissionDenied

from .filters import *
from .models import Requisito, PalabraClave, Propuesta, Area , DatoContacto
from .serializers import RequisitoSerializer, PalabraClaveSerializer, PropuestaSerializer, AreaSerializer, DatoContactoSerializer
import logging
from rest_framework.decorators import action
from rest_framework.response import Response

logger = logging.getLogger(__name__)
class RequisitoViewSet(viewsets.ModelViewSet):
    queryset = Requisito.objects.all()
    serializer_class = RequisitoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = RequisitoFilter

class PalabraClaveViewSet(viewsets.ModelViewSet):
    queryset = PalabraClave.objects.all()
    serializer_class = PalabraClaveSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = PalabrasFilter

class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [permissions.IsAuthenticated]

class DatoContactoViewSet(viewsets.ModelViewSet):
    queryset = DatoContacto.objects.all()
    serializer_class = DatoContactoSerializer
    permission_classes = [permissions.IsAuthenticated]

"""
class PropuestaViewSet(viewsets.ModelViewSet):
    queryset = Propuesta.objects.all()
    serializer_class = PropuestaSerializer
    permission_classes = [permissions.IsAuthenticated]
    

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

"""

class PropuestaViewSet(viewsets.ModelViewSet):
    queryset = Propuesta.objects.all()
    serializer_class = PropuestaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = PropuestaFilter

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.autor != request.user:
            raise PermissionDenied("No tienes permiso para editar esta propuesta")
        
        # Obtener los datos del request
        requisitos_data = request.data.get('requisitos', [])
        palabras_clave_data = request.data.get('palabras_clave', [])
        areas_data = request.data.get('areas', [])
        datos_contacto_data = request.data.get('datos_contacto', [])
        
        # Actualizar la instancia con los datos básicos
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Actualizar relaciones many-to-many
        instance.requisitos.clear()
        for requisito in requisitos_data:
            req, _ = Requisito.objects.get_or_create(descripcion=requisito)
            instance.requisitos.add(req)

        instance.palabras_clave.clear()
        for palabra in palabras_clave_data:
            pc, _ = PalabraClave.objects.get_or_create(palabra=palabra)
            instance.palabras_clave.add(pc)

        instance.areas.clear()
        for area in areas_data:
            a, _ = Area.objects.get_or_create(nombre=area)
            instance.areas.add(a)

        instance.datos_contacto.clear()
        for dato in datos_contacto_data:
            dc, _ = DatoContacto.objects.get_or_create(dato=dato)
            instance.datos_contacto.add(dc)

        return Response(serializer.data)

    def get_queryset(self):
        # Si el usuario está viendo todas las propuestas, solo mostrar las visibles
        if self.action == 'list':
            return Propuesta.objects.filter(visible=True)
        # Para mis_propuestas y otras acciones, mostrar todas las propuestas del usuario
        return Propuesta.objects.all()


    def create(self, request, *args, **kwargs):
        logger.info(f"User: {request.user}")
        logger.info(f"Authenticated: {request.user.is_authenticated}")
        logger.info(f"Request data: {request.data}")
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'profesor'):
            carrera = self.request.user.profesor.departamento
        elif hasattr(self.request.user, 'alumno'):
            carrera = self.request.user.alumno.carrera
        else:
            carrera = ''
        serializer.save(autor=self.request.user, carrera=carrera)
    
    @action(detail=False, methods=['GET'])
    def mis_propuestas(self, request):
        propuestas = Propuesta.objects.filter(autor=request.user)
        serializer = self.get_serializer(propuestas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['PATCH'])
    def toggle_visibility(self, request, pk=None):
        propuesta = self.get_object()
        if propuesta.autor != request.user:
            raise PermissionDenied("No tienes permiso para editar esta propuesta")
        
        visible = request.data.get('visible', None)
        if visible is not None:
            propuesta.visible = visible
            propuesta.save()
        
        return Response(self.get_serializer(propuesta).data)