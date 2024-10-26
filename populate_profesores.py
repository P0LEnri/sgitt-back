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
            password='123',  # Considera usar una contraseña más segura
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

def populate_profesores(num_profesores=15):
    materias = ["Cálculo", "Álgebra Lineal", "Cálculo Aplicado", "Comunicación Oral y Escrita", "Fundamentos de Programación", "Análisis Vectorial", "Matemáticas Discretas", "Fundamentos de Algoritmos y Estructuras de Datos", "Ingeniería, Ética y Sociedad", "Fundamentos Económicos", "Ecuaciones Diferenciales", "Circuitos Eléctricos", "Fundamentos de Diseño Digital", "Bases de Datos", "Finanzas Empresariales", "Paradigmas de Programación", "Análisis y Diseño de Algoritmos", "Probabilidad y Estadística", "Matemáticas Avanzadas para la Ingeniería", "Electrónica Analógica", "Diseño de Sistemas Digitales", "Tecnologías para el Desarrollo de Aplicaciones Web", "Sistemas Operativos", "Teoría de la Computación", "Procesamiento Digital de Señales", "Instrumentación y Control", "Arquitectura de Computadoras", "Análisis y Diseño de Sistemas", "Formulación y Evaluación de Proyectos Informáticos", "Compiladores", "Redes de Computadoras", "Sistemas en Chip", "Optativa A1", "Optativa B1", "Métodos Cuantitativos para la Toma de Decisiones", "Ingeniería de Software", "Inteligencia Artificial", "Aplicaciones para Comunicaciones en Red", "Desarrollo de Aplicaciones Móviles Nativas", "Optativa A2", "Optativa B2", "Trabajo Terminal I", "Sistemas Distribuidos", "Administración de Servicios en Red", "Estancia Profesional", "Desarrollo de Habilidades Sociales para la Alta Dirección", "Trabajo Terminal II", "Gestión Empresarial", "Liderazgo Personal"]

    for i in range(num_profesores):
        email = f"profesor{i+1+0}@ejemplo.com"
        first_name = f"Nombre{i+1+0}"
        last_name = f"Apellido{i+1+0}"
        matricula = f"PROF{100000+i+0}"
        materias_asignadas = ", ".join(random.sample(materias, k=random.randint(1, 3)))
        
        create_profesor(email, first_name, last_name, matricula, materias_asignadas)

if __name__ == '__main__':
    print("Iniciando población de profesores...")
    populate_profesores()
    print("Población de profesores completada.")