from django.db import models
from django.conf import settings

class Requisito(models.Model):
    descripcion = models.CharField(max_length=255)

    def __str__(self):
        return self.descripcion

class PalabraClave(models.Model):
    palabra = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.palabra
    
class Area(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class DatoContacto(models.Model):
    dato = models.CharField(max_length=255)
    
    def __str__(self):
        return self.dato

class Propuesta(models.Model):
    nombre = models.CharField(max_length=255)
    objetivo = models.TextField()
    cantidad_alumnos = models.PositiveIntegerField()
    cantidad_profesores = models.PositiveIntegerField()
    requisitos = models.ManyToManyField(Requisito)
    palabras_clave = models.ManyToManyField(PalabraClave)
    areas = models.ManyToManyField(Area)
    carrera = models.CharField(max_length=100, blank=True)  # Puede ser blanco si es creado por un profesor
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='propuestas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    tipo_propuesta = models.CharField(max_length=50)  # Sin choices
    datos_contacto = models.ManyToManyField(DatoContacto)
    visible = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['fecha_creacion']),
            models.Index(fields=['visible']), 
        ]