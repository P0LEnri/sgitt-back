from django_filters import rest_framework as filters
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Propuesta, Requisito, PalabraClave, Area


class RequisitoFilter(filters.FilterSet):
    descripcion = filters.CharFilter(field_name='descripcion', lookup_expr='')

    class Meta:
        model = Requisito
        fields = ['descripcion']

class PalabrasFilter(filters.FilterSet):
    palabra = filters.CharFilter(field_name='palabra', lookup_expr='icontains')
    class Meta:
        model = PalabraClave
        fields = ['palabra']


class PropuestaFilter(filters.FilterSet):
    nombre = filters.CharFilter(field_name='nombre', lookup_expr='icontains')
    objetivo = filters.CharFilter(field_name='objetivo', lookup_expr='icontains')
    cantidad_alumnos = filters.NumberFilter(field_name='cantidad_alumnos', lookup_expr='exact')
    cantidad_profesores = filters.NumberFilter(field_name='cantidad_profesores')
    start_date = filters.DateFilter(field_name='fecha_creacion', lookup_expr='gte')
    end_date = filters.DateFilter(field_name='fecha_creacion', lookup_expr='lte')
    requisitos = filters.ModelMultipleChoiceFilter(
        queryset=Requisito.objects.all(),
        field_name='requisitos',
        conjoined=False,
    )
    palabras_clave = filters.ModelMultipleChoiceFilter(
        queryset=PalabraClave.objects.all(),
        field_name='palabras_clave',
        conjoined=False,
    )
    areas = filters.ModelMultipleChoiceFilter(
        queryset=Area.objects.all(),
        field_name='areas',
        conjoined=False,
    )
    carrera = filters.CharFilter(field_name='carrera', lookup_expr='icontains')
    autor = filters.ModelChoiceFilter(queryset=get_user_model().objects.all(), field_name='autor')
    tipo_propuesta = filters.CharFilter(field_name='tipo_propuesta', lookup_expr='icontains')
    

    class Meta:
        model = Propuesta
        fields = [
            'nombre',
            'objetivo',
            'cantidad_alumnos',
            'cantidad_profesores',
            'start_date',
            'end_date',
            'requisitos',
            'palabras_clave',
            'areas',
            'carrera',
            'autor',
            'datos_contacto',
            'tipo_propuesta'
        ]
        strict = True