import os
import django
import json
from django.core.exceptions import ObjectDoesNotExist

# Configura el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgitt.settings')
django.setup()

from django.contrib.auth import get_user_model
from usuarios.models import Profesor, Materia, AreaConocimiento

User = get_user_model()

def load_json_data(file_path):
    """Carga los datos del archivo JSON"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def create_materias(materias_data):
    """Crea las materias en la base de datos y devuelve un diccionario con todas ellas"""
    materias_dict = {}
    materias_nombres = set()
    
    # Extraer nombres únicos de materias del JSON
    for profesor in materias_data:
        for materia in profesor['materias']:
            materias_nombres.add(materia['unidad_aprendizaje'])
    
    # Crear materias en la base de datos
    for nombre in materias_nombres:
        materia, created = Materia.objects.get_or_create(nombre=nombre)
        materias_dict[nombre] = materia
        if created:
            print(f"Materia creada: {nombre}")
    
    return materias_dict

def create_profesor(profesor_data, materias_dict):
    try:
        # Crear usuario
        email = profesor_data['correo']
        nombre = profesor_data['nombre']['nombre']
        #nombre = nombres[0]  # Primer nombre
        
        user = User.objects.create_user(
            email=email,
            password='123',
            first_name=nombre,
            last_name=profesor_data['nombre']['apellido_paterno'],
            is_active=True,
            email_verified=True
        )
        
        # Crear profesor
        profesor = Profesor.objects.create(
            user=user,
            apellido_materno=profesor_data['nombre']['apellido_materno'],
            es_profesor=True,
            departamento= profesor_data['departamento'],  
            primer_inicio=True  
        )
        
        # Asignar materias
        materias_asignadas = []
        for materia_data in profesor_data['materias']:
            nombre_materia = materia_data['unidad_aprendizaje']
            if nombre_materia in materias_dict:
                materias_asignadas.append(materias_dict[nombre_materia])
        
        profesor.materias.set(materias_asignadas)
        print(f"Profesor creado: {profesor.user.email} con {len(materias_asignadas)} materias")
        return profesor
    except Exception as e:
        print(f"Error al crear profesor {email}: {str(e)}")
        return None

def populate_profesores(json_file_path):
    # Cargar datos del JSON
    profesores_data = load_json_data(json_file_path)
    
    # Primero creamos o recuperamos todas las materias
    materias_dict = create_materias(profesores_data)
    
    # Crear profesores
    for profesor_data in profesores_data:
        create_profesor(profesor_data, materias_dict)

def clean_database():
    """Limpia la base de datos de profesores y materias"""
    try:
        Profesor.objects.all().delete()
        Materia.objects.all().delete()
        AreaConocimiento.objects.all().delete()
        User.objects.filter(email__contains="@yopmail.com").delete() # Se borran tambien los alumnos xd si se quieren borrar los profesores descomentar esta linea
        User.objects.filter(email__contains="@ejemplo.com").delete()
        print("Base de datos limpiada exitosamente")
    except Exception as e:
        print(f"Error al limpiar la base de datos: {str(e)}")

if __name__ == '__main__':
    json_file_path = 'profesores_procesados.json'  # Asegúrate de que la ruta sea correcta
    
    print("¿Deseas limpiar la base de datos antes de poblarla? (s/n)")
    if input().lower() == 's':
        clean_database()
    
    print("Iniciando población de profesores...")
    populate_profesores(json_file_path)
    print("Población de profesores completada.")