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

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # if instance.autor != request.user:
        #     raise PermissionDenied("No tienes permiso para editar esta propuesta")
        
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
        if self.request.path.startswith('/api/crud/propuestas') or self.request.user.is_admin:
            return Propuesta.objects.all()
            
        # Para el resto de las vistas, solo mostrar propuestas visibles
        if self.action == 'list':
            return Propuesta.objects.filter(visible=True)
            
        return Propuesta.objects.all()
    
    def get_queryadmin(self):
        queryset = Propuesta.objects.select_related('autor').all()
        if self.action == 'list':
            return queryset.filter(visible=True)
        return queryset

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
        # if propuesta.autor != request.user:
        #     raise PermissionDenied("No tienes permiso para editar esta propuesta")
        
        visible = request.data.get('visible', None)
        if visible is not None:
            propuesta.visible = visible
            propuesta.save()
        
        return Response(self.get_serializer(propuesta).data)
    
    @action(detail=False, methods=['GET'])
    def admin_list(self, request):
        queryset = Propuesta.objects.select_related('autor').all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
# propuestas/views.py

class PropuestaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Propuesta.objects.all()
    serializer_class = PropuestaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Para vistas del admin, siempre mostrar todas las propuestas
        if self.request.user.is_admin:
            return Propuesta.objects.all()
        # Para usuarios normales, solo mostrar propuestas visibles
        return Propuesta.objects.filter(visible=True)

    def get_object(self):
        obj = super().get_object()
        # Los administradores pueden editar cualquier propuesta
        if self.request.user.is_admin:
            return obj
        # Para usuarios normales, verificar si son el autor
        if not request.user.is_admin and instance.autor != request.user:
            raise PermissionDenied("No tienes permiso para editar esta propuesta 1")
        return obj

    def perform_update(self, serializer):
        instance = self.get_object()  # Esto ya hace la verificación de permisos
        data = self.request.data

        try:
            # Actualizar campos básicos
            instance.nombre = data.get('nombre', instance.nombre)
            instance.objetivo = data.get('objetivo', instance.objetivo)
            instance.cantidad_alumnos = int(data.get('cantidad_alumnos', instance.cantidad_alumnos))
            instance.cantidad_profesores = int(data.get('cantidad_profesores', instance.cantidad_profesores))
            instance.tipo_propuesta = data.get('tipo_propuesta', instance.tipo_propuesta)
            
            # Solo los administradores pueden cambiar la visibilidad
            if self.request.user.is_admin:
                instance.visible = data.get('visible', instance.visible)

            # Actualizar datos de relaciones si se proporcionaron
            if 'requisitos' in data:
                instance.requisitos.clear()
                for requisito in data['requisitos']:
                    req, _ = Requisito.objects.get_or_create(descripcion=requisito)
                    instance.requisitos.add(req)

            if 'palabras_clave' in data:
                instance.palabras_clave.clear()
                for palabra in data['palabras_clave']:
                    pc, _ = PalabraClave.objects.get_or_create(palabra=palabra)
                    instance.palabras_clave.add(pc)

            if 'areas' in data:
                instance.areas.clear()
                for area in data['areas']:
                    a, _ = Area.objects.get_or_create(nombre=area)
                    instance.areas.add(a)

            if 'datos_contacto' in data:
                instance.datos_contacto.clear()
                for dato in data['datos_contacto']:
                    dc, _ = DatoContacto.objects.get_or_create(dato=dato)
                    instance.datos_contacto.add(dc)

            instance.save()
            return instance

        except Exception as e:
            raise serializers.ValidationError(f"Error al actualizar la propuesta: {str(e)}")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        if not request.user.is_admin and instance.autor != request.user:
            raise PermissionDenied("No tienes permiso para editar esta propuesta 2")
        
        try:
            updated_instance = self.perform_update(serializer)
            serializer = self.get_serializer(updated_instance)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def create(self, request, *args, **kwargs):
        try:
            # Verificar si el usuario es admin
            if not request.user.is_admin:
                raise PermissionDenied("Solo los administradores pueden crear propuestas desde el panel admin")

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Crear la propuesta con los datos básicos
            propuesta = Propuesta.objects.create(
                nombre=request.data.get('nombre'),
                objetivo=request.data.get('objetivo'),
                cantidad_alumnos=request.data.get('cantidad_alumnos', 1),
                cantidad_profesores=request.data.get('cantidad_profesores', 1),
                tipo_propuesta=request.data.get('tipo_propuesta', 'TT1'),
                visible=request.data.get('visible', True),
                autor=request.user
            )

            # Si hay un autor específico proporcionado en los datos
            autor_id = request.data.get('autor_id')
            if autor_id:
                try:
                    autor = get_user_model().objects.get(id=autor_id)
                    propuesta.autor = autor
                    propuesta.save()
                except get_user_model().DoesNotExist:
                    pass

            return Response(self.get_serializer(propuesta).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not request.user.is_admin and instance.autor != request.user:
            raise PermissionDenied("No tienes permiso para eliminar esta propuesta")
        
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