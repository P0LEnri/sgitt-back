import os
import django
import random
from django.core.exceptions import ObjectDoesNotExist

# Configura el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgitt.settings')
django.setup()

from django.contrib.auth import get_user_model
from usuarios.models import Profesor

User = get_user_model()

def create_profesor(email, first_name, last_name, matricula, materias):
    try:
        user = User.objects.create_user(
            email=email,
            password='password123',  # Considera usar una contraseña más segura
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            email_verified=True
        )
        profesor = Profesor.objects.create(
            user=user,
            matricula=matricula,
            materias=materias,
            es_profesor=True
        )
        print(f"Profesor creado: {profesor.user.email}")
        return profesor
    except Exception as e:
        print(f"Error al crear profesor {email}: {str(e)}")
        return None

def populate_profesores(num_profesores=10):
    materias = [
        "Programación", "Bases de Datos", "Inteligencia Artificial",
        "Redes", "Sistemas Operativos", "Algoritmos", "Estructura de Datos",
        "Ingeniería de Software", "Seguridad Informática", "Aprendizaje Automático"
    ]

    for i in range(num_profesores):
        email = f"profesor{i+1}@ejemplo.com"
        first_name = f"Nombre{i+1}"
        last_name = f"Apellido{i+1}"
        matricula = f"PROF{100000+i}"
        materias_asignadas = ", ".join(random.sample(materias, k=random.randint(1, 3)))
        
        create_profesor(email, first_name, last_name, matricula, materias_asignadas)

if __name__ == '__main__':
    print("Iniciando población de profesores...")
    populate_profesores()
    print("Población de profesores completada.")