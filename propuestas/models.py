from django.db import models
from usuarios.models import Alumno, Profesor

class Propuesta(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    author = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='open')