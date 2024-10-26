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

    class Meta:
        model = Alumno
        fields = ('email', 'password', 'confirmPassword', 'nombre', 'apellido_paterno', 'apellido_materno', 'boleta', 'carrera', 'plan_estudios', 'areas_alumno', 'areas_ids')

    def validate(self, data):
        if data['password'] != data['confirmPassword']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data

    def create(self, validated_data):
        user_data = validated_data.pop('user', {})
        password = validated_data.pop('password')
        validated_data.pop('confirmPassword')
        areas_ids = validated_data.pop('areas_ids', [])
        
        user = User.objects.create_user(
            email=user_data.get('email'),
            password=password,
            first_name=user_data.get('first_name'),
            last_name=user_data.get('last_name'),
            is_active=False,
            email_verified=False 
        )
        
        alumno = Alumno.objects.create(user=user, **validated_data)
        if areas_ids:
            alumno.areas_alumno.set(areas_ids)
        
        self.send_verification_email(user)
        
        return alumno

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
    apellido = serializers.CharField(source='user.last_name')
    password = serializers.CharField(write_only=True, required=False)
    confirmPassword = serializers.CharField(write_only=True, required=False)
    materias = MateriaSerializer(many=True, read_only=True)
    materias_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )


    class Meta:
        model = Profesor
        fields = ('id', 'email', 'nombre', 'apellido', 'password', 'confirmPassword', 'materias', 'materias', 'materias_ids', 'es_profesor')


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
        return profesor

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if 'email' in user_data:
            instance.user.email = user_data['email']
        if 'first_name' in user_data:
            instance.user.first_name = user_data['first_name']
        if 'last_name' in user_data:
            instance.user.last_name = user_data['last_name']
        instance.user.save()

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['email'] = instance.user.email
        representation['nombre'] = instance.user.first_name
        representation['apellido'] = instance.user.last_name
        return representation