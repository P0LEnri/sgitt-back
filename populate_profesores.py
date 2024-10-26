import os
import django
import random
from django.core.exceptions import ObjectDoesNotExist

# Configura el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgitt.settings')
django.setup()

from django.contrib.auth import get_user_model
from usuarios.models import Profesor, Materia

User = get_user_model()

def create_materias():
    """Crea las materias en la base de datos y devuelve un diccionario con todas ellas"""
    materias_nombres = [
        "Cálculo", "Álgebra Lineal", "Cálculo Aplicado", "Comunicación Oral y Escrita",
        "Fundamentos de Programación", "Análisis Vectorial", "Matemáticas Discretas",
        "Fundamentos de Algoritmos y Estructuras de Datos", "Ingeniería, Ética y Sociedad",
        "Fundamentos Económicos", "Ecuaciones Diferenciales", "Circuitos Eléctricos",
        "Fundamentos de Diseño Digital", "Bases de Datos", "Finanzas Empresariales",
        "Paradigmas de Programación", "Análisis y Diseño de Algoritmos",
        "Probabilidad y Estadística", "Matemáticas Avanzadas para la Ingeniería",
        "Electrónica Analógica", "Diseño de Sistemas Digitales",
        "Tecnologías para el Desarrollo de Aplicaciones Web", "Sistemas Operativos",
        "Teoría de la Computación", "Procesamiento Digital de Señales",
        "Instrumentación y Control", "Arquitectura de Computadoras",
        "Análisis y Diseño de Sistemas", "Formulación y Evaluación de Proyectos Informáticos",
        "Compiladores", "Redes de Computadoras", "Sistemas en Chip", "Optativa A1",
        "Optativa B1", "Métodos Cuantitativos para la Toma de Decisiones",
        "Ingeniería de Software", "Inteligencia Artificial",
        "Aplicaciones para Comunicaciones en Red", "Desarrollo de Aplicaciones Móviles Nativas",
        "Optativa A2", "Optativa B2", "Trabajo Terminal I", "Sistemas Distribuidos",
        "Administración de Servicios en Red", "Estancia Profesional",
        "Desarrollo de Habilidades Sociales para la Alta Dirección", "Trabajo Terminal II",
        "Gestión Empresarial", "Liderazgo Personal"
    ]
    
    materias_dict = {}
    for nombre in materias_nombres:
        materia, created = Materia.objects.get_or_create(nombre=nombre)
        materias_dict[nombre] = materia
        if created:
            print(f"Materia creada: {nombre}")
    
    return materias_dict

def create_profesor(email, first_name, last_name, matricula, materias_list):
    try:
        # Crear usuario
        user = User.objects.create_user(
            email=email,
            password='123',  # Considera usar una contraseña más segura
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            email_verified=True
        )
        
        # Crear profesor
        profesor = Profesor.objects.create(
            user=user,
            
            es_profesor=True
        )
        
        # Asignar materias
        profesor.materias.set(materias_list)
        print(f"Profesor creado: {profesor.user.email} con {len(materias_list)} materias")
        return profesor
    except Exception as e:
        print(f"Error al crear profesor {email}: {str(e)}")
        return None

def populate_profesores(num_profesores=100):
    # Primero creamos o recuperamos todas las materias
    materias_dict = create_materias()
    materias_list = list(materias_dict.values())
    
    for i in range(num_profesores):
        email = f"profesor{i+1}@ejemplo.com"
        first_name = f"Nombre{i+1}"
        last_name = f"Apellido{i+1}"
        matricula = f"PROF{100000+i}"
        
        # Seleccionar aleatoriamente entre 1 y 3 materias
        materias_asignadas = random.sample(materias_list, k=random.randint(1, 3))
        
        create_profesor(email, first_name, last_name, matricula, materias_asignadas)

def clean_database():
    """Limpia la base de datos de profesores y materias"""
    try:
        Profesor.objects.all().delete()
        Materia.objects.all().delete()
        User.objects.filter(email__contains="@ejemplo.com").delete()
        print("Base de datos limpiada exitosamente")
    except Exception as e:
        print(f"Error al limpiar la base de datos: {str(e)}")

if __name__ == '__main__':
    print("¿Deseas limpiar la base de datos antes de poblarla? (s/n)")
    if input().lower() == 's':
        clean_database()
    
    print("Iniciando población de profesores...")
    populate_profesores()
    print("Población de profesores completada.")