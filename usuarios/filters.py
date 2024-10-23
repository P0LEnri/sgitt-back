from django_filters import rest_framework as filters

from usuarios.models import Alumno, Profesor
from django.db.models import Q
class AlumnoSearchFilter(filters.Filter):
    def filter(self, queryset, value):
        if value:
            if "@" in value:
                return queryset.filter(user__email__icontains=value)
            elif value.isdigit():
                return queryset.filter(boleta__icontains=value)
            else:
                return queryset.filter(Q(user__first_name__icontains=value) |
                                       Q(user__last_name__icontains=value) |
                                       Q(materno__icontains=value))
        return queryset


class ProfesorSearchFilter(filters.Filter):
    def filter(self, queryset, value):
        if value:
            if "@" in value:
                return queryset.filter(user__email__icontains=value)
            elif value.isdigit():
                return queryset.filter(matricula__icontains=value)
            else:
                return queryset.filter(Q(user__first_name__icontains=value) |
                                       Q(user__last_name__icontains=value))

        return queryset

class AlumnoFilter(filters.FilterSet):
    usuario = AlumnoSearchFilter()
    carrera = filters.ChoiceFilter(choices=Alumno.Carrera.choices, field_name='carrera')
    plan_estudios = filters.CharFilter(field_name='plan_estudios', lookup_expr='icontains')
    class Meta:
        model = Alumno
        fields = ['usuario', 'carrera', 'plan_estudios']

class ProfesorFilter(filters.FilterSet):
    usuario = ProfesorSearchFilter()
    materias = filters.CharFilter(field_name='materias', lookup_expr='icontains')
    class Meta:
        model = Profesor
        fields = ['usuario', 'materias']