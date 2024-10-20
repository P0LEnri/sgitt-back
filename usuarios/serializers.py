from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Alumno, Profesor
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()

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

    class Meta:
        model = Alumno
        fields = ('email', 'password', 'confirmPassword', 'nombre', 'apellido_paterno', 'apellido_materno', 'boleta', 'carrera', 'plan_estudios')

    def validate(self, data):
        if data['password'] != data['confirmPassword']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data

    def create(self, validated_data):
        user_data = validated_data.pop('user', {})
        password = validated_data.pop('password')
        validated_data.pop('confirmPassword')
        
        user = User.objects.create_user(
            email=user_data.get('email'),
            password=password,
            first_name=user_data.get('first_name'),
            last_name=user_data.get('last_name'),
            is_active=False,
            email_verified=False 
        )
        
        alumno = Alumno.objects.create(user=user, **validated_data)
        
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

class ProfesorSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email')
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)

    class Meta:
        model = Profesor
        fields = ['id', 'nombre', 'email', 'matricula', 'materias', 'first_name', 'last_name']

    def create(self, validated_data):
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        email = validated_data.pop('email')
        
        User = get_user_model()
        user = User.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        profesor = Profesor.objects.create(user=user, **validated_data)
        return profesor

    def update(self, instance, validated_data):
        user_data = {}
        if 'email' in validated_data:
            user_data['email'] = validated_data.pop('email')
        if 'first_name' in validated_data:
            user_data['first_name'] = validated_data.pop('first_name')
        if 'last_name' in validated_data:
            user_data['last_name'] = validated_data.pop('last_name')
        
        if user_data:
            User.objects.filter(id=instance.user.id).update(**user_data)
        
        return super().update(instance, validated_data)