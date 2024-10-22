from django.contrib import admin
from .models import Requisito, PalabraClave, Propuesta

@admin.register(Requisito)
class RequisitoAdmin(admin.ModelAdmin):
    list_display = ['descripcion']
    search_fields = ['descripcion']

@admin.register(PalabraClave)
class PalabraClaveAdmin(admin.ModelAdmin):
    list_display = ['palabra']
    search_fields = ['palabra']

@admin.register(Propuesta)
class PropuestaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'autor', 'cantidad_alumnos', 'cantidad_profesores', 'fecha_creacion']
    list_filter = ['fecha_creacion', 'cantidad_alumnos', 'cantidad_profesores']
    search_fields = ['nombre', 'objetivo', 'autor__email']
    filter_horizontal = ['requisitos', 'palabras_clave']