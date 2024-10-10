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
    email = serializers.EmailField(source='user.email', read_only=True)
    nombre = serializers.CharField(source='user.first_name', read_only=True)
    apellido_paterno = serializers.CharField(source='user.last_name', read_only=True)
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
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        validated_data.pop('confirmPassword')  # Removemos confirmPassword ya que no lo necesitamos para crear el usuario
        nombre = validated_data.pop('nombre')
        apellido_paterno = validated_data.pop('apellido_paterno')
        apellido_materno = validated_data.pop('apellido_materno')
        
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=nombre,
            last_name=apellido_paterno,
            is_active=False,
            email_verified=False 
        )
        
        alumno = Alumno.objects.create(user=user, apellido_materno=apellido_materno, **validated_data)
        
        self.send_verification_email(user)
        
        return alumno
    
    
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
    user = UserSerializer()

    class Meta:
        model = Profesor
        fields = '__all__'

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        User = get_user_model()
        user = User.objects.create(**user_data)
        profesor = Profesor.objects.create(user=user, **validated_data)

        return profesor