import os
import django
import sys

# Configura el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgitt.settings')
django.setup()

from django.contrib.auth import get_user_model
from usuarios.models import CustomUser

def create_admin_user():
    User = get_user_model()
    
    # Verifica si ya existe un usuario admin
    if User.objects.filter(email='admin@sgitt.com').exists():
        print("El usuario administrador ya existe.")
        return
    
    try:
        admin_user = User.objects.create_user(
            email='admin@sgitt.com',
            password='admin123',
            first_name='Admin',
            last_name='SGITT',
            is_active=True,
            is_staff=True,
            is_superuser=True,
            is_admin=True,
            email_verified=True
        )
        print(f"Usuario administrador creado exitosamente con email: {admin_user.email}")
        print("Contraseña: admin123")
    except Exception as e:
        print(f"Error al crear el usuario administrador: {e}")

if __name__ == "__main__":
    create_admin_user()