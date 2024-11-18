# SGITT Backend

## Descripción

Sistema de Gestión Integral para Trabajo Terminal (SGITT) Backend es una API REST desarrollada en Django que proporciona la infraestructura necesaria para gestionar propuestas de trabajos terminales, usuarios, y comunicaciones entre alumnos y profesores del IPN.

## Características Principales

- 🔐 **Sistema de Autenticación**
  - JWT Authentication
  - Email verification
  - Gestión de roles (Alumno/Profesor)
  - Renovación de tokens

- 👥 **Gestión de Usuarios**
  - Perfiles diferenciados para alumnos y profesores
  - Sistema de áreas de conocimiento y materias
  - Validación de correos institucionales
  - Embeddings para búsqueda semántica

- 📝 **Sistema de Propuestas**
  - CRUD completo de propuestas
  - Sistema de filtrado avanzado
  - Control de visibilidad
  - Gestión de requisitos y palabras clave

- 💬 **Sistema de Chat en Tiempo Real**
  - WebSockets para mensajería instantánea
  - Gestión de conversaciones
  - Sistema de notificaciones
  - Marcado de mensajes leídos

## Tecnologías Utilizadas

- [Django 5.1](https://www.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Channels](https://channels.readthedocs.io/)
- [SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- [MySQL](https://www.mysql.com/)
- [Sentence Transformers](https://www.sbert.net/)

## Requisitos Previos

- Python 3.10 o superior
- MySQL 8.0 o superior
- Redis (para WebSockets)
- Virtualenv

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/sgitt-back.git
cd sgitt-back
```

2. Crear y activar entorno virtual:
```bash
python -m venv env
source env/bin/activate  # En Windows: env\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
Crear archivo `.env` en la raíz del proyecto:
```env
DB_ENGINE=django.db.backends.mysql
DB_NAME=sgitt_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

5. Realizar migraciones:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Cargar datos iniciales (opcional):
```bash
python populate_profesores.py
```

7. Crear superusuario:
```bash
python manage.py createsuperuser
```

8. Iniciar servidor:
```bash
python manage.py runserver
```

## Estructura del Proyecto

```
sgitt-back/
├── sgitt/              # Configuración principal del proyecto
├── usuarios/           # App de gestión de usuarios
├── propuestas/        # App de gestión de propuestas
├── chat/              # App de sistema de chat
├── requirements.txt   # Dependencias del proyecto
└── manage.py         # Script de gestión de Django
```

## APIs Principales

### Usuarios
- `POST /api/register/` - Registro de usuarios
- `POST /api/login/` - Inicio de sesión
- `GET /api/verify-email/<token>/` - Verificación de email
- `GET /api/profesores/buscar/` - Búsqueda semántica de profesores

### Propuestas
- `GET /api/propuestas/` - Listar propuestas
- `POST /api/propuestas/` - Crear propuesta
- `GET /api/propuestas/mis_propuestas/` - Propuestas del usuario
- `PATCH /api/propuestas/<id>/toggle_visibility/` - Cambiar visibilidad

### Chat
- `GET /api/chat/conversations/` - Listar conversaciones
- `POST /api/chat/messages/` - Enviar mensaje
- `WebSocket /ws/chat/<conversation_id>/` - Chat en tiempo real

## Configuración de Desarrollo

### Configurar MySQL
```sql
CREATE DATABASE sgitt_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sgitt_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON sgitt_db.* TO 'sgitt_user'@'localhost';
FLUSH PRIVILEGES;
```

### Configurar Redis (para WebSockets)
```bash
sudo apt-get install redis-server  # En Ubuntu/Debian
redis-cli ping  # Debería responder PONG
```

## Testing

```bash
python manage.py test
```

## Despliegue

1. Configurar variables de entorno de producción
2. Recolectar archivos estáticos:
```bash
python manage.py collectstatic
```
3. Configurar Gunicorn y nginx
4. Configurar supervisor para Daphne (WebSockets)

## Mantenimiento

- Backups de base de datos:
```bash
python manage.py dumpdata > backup.json
```


## Contribuir

1. Fork del repositorio
2. Crear rama de feature (`git checkout -b feature/NuevaCaracteristica`)
3. Commit de cambios (`git commit -m 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Crear Pull Request


## Licencia

Este proyecto está bajo la Licencia MIT.

## Contacto

- Nombre del Equipo - TT 2024 B163
- Email del Proyecto - sgitt2002@gmail.com

## Agradecimientos

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Sentence Transformers](https://www.sbert.net/)