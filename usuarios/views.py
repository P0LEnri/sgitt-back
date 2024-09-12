from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Alumno
from .serializers import AlumnoSerializer

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    print(request.data)
    serializer = AlumnoSerializer(data=request.data)
    if serializer.is_valid():
        try:
            alumno = serializer.save()
            return Response({"message": "Usuario registrado exitosamente"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    correo = request.data.get('email')
    password = request.data.get('password')
    user = authenticate(email=correo, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_type': 'alumno' if hasattr(user, 'alumno') else 'profesor'
        })
    return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)