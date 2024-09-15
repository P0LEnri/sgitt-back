from rest_framework import viewsets, permissions
from .models import Requisito, PalabraClave, Propuesta
from .serializers import RequisitoSerializer, PalabraClaveSerializer, PropuestaSerializer

class RequisitoViewSet(viewsets.ModelViewSet):
    queryset = Requisito.objects.all()
    serializer_class = RequisitoSerializer
    permission_classes = [permissions.IsAuthenticated]

class PalabraClaveViewSet(viewsets.ModelViewSet):
    queryset = PalabraClave.objects.all()
    serializer_class = PalabraClaveSerializer
    permission_classes = [permissions.IsAuthenticated]

"""
class PropuestaViewSet(viewsets.ModelViewSet):
    queryset = Propuesta.objects.all()
    serializer_class = PropuestaSerializer
    permission_classes = [permissions.IsAuthenticated]
    

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

"""

import logging

logger = logging.getLogger(__name__)

class PropuestaViewSet(viewsets.ModelViewSet):
    queryset = Propuesta.objects.all()
    serializer_class = PropuestaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        logger.info(f"User: {request.user}")
        logger.info(f"Authenticated: {request.user.is_authenticated}")
        logger.info(f"Request data: {request.data}")
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)    