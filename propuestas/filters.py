from django_filters import rest_framework as filters
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Propuesta, Requisito, PalabraClave


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
    start_date = filters.DateFilter(field_name='fecha_creacion', lookup_expr='gte')  # Fecha de inicio (mayor o igual que)
    end_date = filters.DateFilter(field_name='fecha_creacion', lookup_expr='lte')  # Fecha de fin (menor o igual que)
    requisitos = filters.ModelMultipleChoiceFilter(
        queryset=Requisito.objects.all(),
        field_name='requisitos',
        conjoined=False,  # Cambiar a True si quieres que coincidan todos los requisitos
    )
    palabras_clave = filters.ModelMultipleChoiceFilter(
        queryset=PalabraClave.objects.all(),
        field_name='palabras_clave',
        conjoined=False,  # Cambiar a True si quieres que coincidan todas las palabras clave
    )
    autor = filters.ModelChoiceFilter(queryset=get_user_model().objects.all(), field_name='autor')

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
            'autor'
        ]
        strict = True