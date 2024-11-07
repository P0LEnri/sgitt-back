from rest_framework import viewsets, permissions, generics, status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied

from .filters import *
from .models import Requisito, PalabraClave, Propuesta, Area , DatoContacto
from .serializers import RequisitoSerializer, PalabraClaveSerializer, PropuestaSerializer, AreaSerializer, DatoContactoSerializer
import logging
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
    
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from .models import Propuesta
from .serializers import PropuestaSerializer


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

    def get_queryset(self):
        queryset = Propuesta.objects.select_related('autor').all()
        if self.action == 'list':
            return queryset.filter(visible=True)
        return queryset

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'profesor'):
            carrera = self.request.user.profesor.departamento
        elif hasattr(self.request.user, 'alumno'):
            carrera = self.request.user.alumno.carrera
        else:
            carrera = ''
        serializer.save(autor=self.request.user, carrera=carrera)

    @action(detail=False, methods=['GET'])
    def admin_list(self, request):
        queryset = Propuesta.objects.select_related('autor').all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def mis_propuestas(self, request):
        propuestas = Propuesta.objects.filter(autor=request.user)
        serializer = self.get_serializer(propuestas, many=True)
        return Response(serializer.data)
    
class PropuestaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Propuesta.objects.all()
    serializer_class = PropuestaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj = super().get_object()
        # Puedes agregar lógica adicional aquí si es necesario
        return obj

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_propuesta(request, pk):
    try:
        propuesta = Propuesta.objects.get(pk=pk)
        propuesta.delete()
        return Response(status=204)
    except Propuesta.DoesNotExist:
        return Response(status=404)    


    # def perform_update(self, serializer):
    #     if not self.request.user.is_staff and serializer.instance.autor != self.request.user:
    #         raise PermissionDenied("No tienes permiso para editar esta propuesta")
    #     serializer.save()

    # def perform_destroy(self, instance):
    #     if not self.request.user.is_staff and instance.autor != self.request.user:
    #         raise PermissionDenied("No tienes permiso para eliminar esta propuesta")
    #     instance.delete()