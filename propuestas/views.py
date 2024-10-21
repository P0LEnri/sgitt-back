from rest_framework import viewsets, permissions

from .filters import *
from .models import Requisito, PalabraClave, Propuesta, Area
from .serializers import RequisitoSerializer, PalabraClaveSerializer, PropuestaSerializer, AreaSerializer
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

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset

    def create(self, request, *args, **kwargs):
        logger.info(f"User: {request.user}")
        logger.info(f"Authenticated: {request.user.is_authenticated}")
        logger.info(f"Request data: {request.data}")
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        carrera = ''
        if hasattr(self.request.user, 'alumno'):
            carrera = self.request.user.alumno.carrera
        serializer.save(autor=self.request.user, carrera=carrera)
    
    @action(detail=False, methods=['GET'])
    def mis_propuestas(self, request):
        propuestas = Propuesta.objects.filter(autor=request.user)
        serializer = self.get_serializer(propuestas, many=True)
        return Response(serializer.data)