from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Alumno, Profesor

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name')
        extra_kwargs = {'password': {'write_only': True}}

class AlumnoSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    nombre = serializers.CharField()
    apellido_paterno = serializers.CharField()
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
            last_name=f"{apellido_paterno} {apellido_materno}".strip()
        )
        
        return Alumno.objects.create(user=user, **validated_data)

class ProfesorSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Profesor
        fields = '__all__'