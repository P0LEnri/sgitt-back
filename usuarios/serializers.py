from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Alumno, Profesor,AreaConocimiento,Materia
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()

class AreaConocimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaConocimiento
        fields = ['id', 'nombre']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name')
        extra_kwargs = {'password': {'write_only': True}}

class AlumnoSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    nombre = serializers.CharField(source='user.first_name')
    apellido_paterno = serializers.CharField(source='user.last_name')
    apellido_materno = serializers.CharField()
    password = serializers.CharField(write_only=True)
    confirmPassword = serializers.CharField(write_only=True)
    areas_alumno = AreaConocimientoSerializer(many=True, read_only=True)
    areas_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    areas_custom = serializers.ListField(child=serializers.CharField(), write_only=True, required=False, default=[])
    is_admin = serializers.BooleanField(source='user.is_admin', required=False)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = Alumno
        fields = ('id', 'email', 'password', 'confirmPassword', 'nombre', 'apellido_paterno', 'apellido_materno', 'boleta', 'carrera', 'plan_estudios', 'areas_alumno', 'areas_ids', 'areas_custom', 'user_id', 'is_admin')

    def validate(self, data):
        # Solo validar contraseñas si están presentes en los datos
        if 'password' in data and 'confirmPassword' in data:
            if data['password'] != data['confirmPassword']:
                raise serializers.ValidationError("Las contraseñas no coinciden")
        return data

    def create(self, validated_data):
        user_data = validated_data.pop('user', {})
        password = validated_data.pop('password')
        validated_data.pop('confirmPassword')
        areas_ids = validated_data.pop('areas_ids', [])
        areas_custom = validated_data.pop('areas_custom', [])
        print("Areas IDs recibidas:", areas_ids)
        print("Areas custom recibidas:", areas_custom)
        
        user = User.objects.create_user(
            email=user_data.get('email'),
            password=password,
            first_name=user_data.get('first_name'),
            last_name=user_data.get('last_name'),
            is_active=False,
            email_verified=False
        )
        
        alumno = Alumno.objects.create(user=user, **validated_data)
        # Procesar las materias seleccionadas y convertirlas en áreas
        if areas_ids:
            for materia_id in areas_ids:
                try:
                    materia = Materia.objects.get(id=materia_id)
                    print("Materia encontrada:", materia)
                    # Crear o obtener un área de conocimiento basada en la materia
                    area, created = AreaConocimiento.objects.get_or_create(
                        nombre=materia.nombre
                    )
                    print("Área creada:", area)
                    alumno.areas_alumno.add(area)
                except Materia.DoesNotExist:
                    continue
        
        for area_nombre in areas_custom:
            area, created = AreaConocimiento.objects.get_or_create(nombre=area_nombre)
            alumno.areas_alumno.add(area)
        
        self.send_verification_email(user)
        
        return alumno
    
    def update(self, instance, validated_data):
        areas_ids = validated_data.pop('areas_ids', [])
        areas_custom = validated_data.pop('areas_custom', [])
        user_data = validated_data.pop('user', {})


        # Actualizar áreas
        instance.areas_alumno.clear()
        for materia_id in areas_ids:
            try:
                materia = Materia.objects.get(id=materia_id)
                area, _ = AreaConocimiento.objects.get_or_create(
                    nombre=materia.nombre
                )
                instance.areas_alumno.add(area)
            except Materia.DoesNotExist:
                continue

        for area_nombre in areas_custom:
            area, _ = AreaConocimiento.objects.get_or_create(nombre=area_nombre)
            instance.areas_alumno.add(area)
            
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        
        # Asegurarse de que is_admin se procese correctamente
        if 'is_admin' in user_data:
            user.is_admin = user_data['is_admin']
        user.save()

        # Actualizar alumno
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['email'] = instance.user.email
        representation['nombre'] = instance.user.first_name
        representation['apellido_paterno'] = instance.user.last_name
        return representation
    
    
    def send_verification_email(self, user):
        verification_link = f"{settings.FRONTEND_URL}/verify-email/{user.verification_token}"
        send_mail(
            'Verifica tu correo electrónico',
            f'Por favor, verifica tu correo electrónico haciendo clic en el siguiente enlace: {verification_link}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=f'''
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                        <h2 style="color: #4a5568;">Verifica tu correo electrónico</h2>
                        <p>Gracias por registrarte. Para completar tu registro, por favor verifica tu correo electrónico haciendo clic en el siguiente botón:</p>
                        <a href="{verification_link}" style="display: inline-block; padding: 10px 20px; background-color: #4299e1; color: white; text-decoration: none; border-radius: 5px;">Verificar Correo</a>
                        <p>Si el botón no funciona, puedes copiar y pegar el siguiente enlace en tu navegador:</p>
                        <p>{verification_link}</p>
                        <p>Si no has solicitado este registro, puedes ignorar este mensaje.</p>
                    </div>
                </body>
            </html>
            '''
    )
        
class MateriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materia
        fields = ['id', 'nombre']

class ProfesorSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email')
    nombre = serializers.CharField(source='user.first_name')
    apellido_paterno = serializers.CharField(source='user.last_name')
    apellido_materno = serializers.CharField()
    password = serializers.CharField(write_only=True, required=False)
    confirmPassword = serializers.CharField(write_only=True, required=False)
    materias = MateriaSerializer(many=True, read_only=True)
    materias_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    areas_profesor = AreaConocimientoSerializer(many=True, read_only=True)
    areas_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        default=[]
    )
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    is_admin = serializers.BooleanField(source='user.is_admin', required=False)


    class Meta:
        model = Profesor
        fields = ('id', 'user_id','email', 'nombre', 'apellido_paterno', 'apellido_materno', 'password', 'confirmPassword', 'materias', 'materias', 'materias_ids', 'areas_profesor', 'areas_ids','es_profesor', 'departamento', 
                 'primer_inicio', 'disponibilidad', 'is_admin')


    def validate(self, data):
        if 'password' in data:
            if data['password'] != data.get('confirmPassword'):
                raise serializers.ValidationError("Las contraseñas no coinciden")
        return data

    def create(self, validated_data):
        user_data = {}
        user_data['email'] = validated_data.pop('user', {}).get('email')
        user_data['first_name'] = validated_data.pop('user', {}).get('first_name')
        user_data['last_name'] = validated_data.pop('user', {}).get('last_name')
        password = validated_data.pop('password', None)
        validated_data.pop('confirmPassword', None)
        materias_ids = validated_data.pop('materias_ids', [])
        materias_ids = validated_data.pop('materias_ids', [])
        areas_ids = validated_data.pop('areas_ids', [])
        
        User = get_user_model()
        user = User.objects.create_user(
            email=user_data['email'],
            password=password,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            is_active=True,  # Los profesores podrían no necesitar verificación de email
            email_verified=True
        )
        
        profesor = Profesor.objects.create(user=user, **validated_data)
        if materias_ids:
            profesor.materias.set(materias_ids)
        if areas_ids:
            profesor.areas_profesor.set(areas_ids)
        return profesor

    def update(self, instance, validated_data):
        # Obtener los IDs de materias y áreas del request data original
        materias_ids = self.context['request'].data.get('materias_ids', [])
        areas_custom = self.context['request'].data.get('areas_custom', [])
        
        # Actualizar las materias si se proporcionaron
        if materias_ids:
            instance.materias.clear()
            instance.materias.set(materias_ids)
        
        
        # Actualizar las áreas de conocimiento
        # Si areas_custom es una lista vacía o None, limpiamos las áreas
        if areas_custom is not None:  # Solo actuamos si el campo fue proporcionado
            instance.areas_profesor.clear()
            # Si hay áreas nuevas, las añadimos
            if areas_custom:
                for area_nombre in areas_custom:
                    area, created = AreaConocimiento.objects.get_or_create(nombre=area_nombre)
                    instance.areas_profesor.add(area)
        
        # Actualizar otros campos si es necesario
        if 'user' in validated_data:
            user_data = validated_data.pop('user')
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        
        # Actualizar campos directos del profesor
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['email'] = instance.user.email
        representation['nombre'] = instance.user.first_name
        representation['apellido'] = instance.user.last_name
        return representation
    
    