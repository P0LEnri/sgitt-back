from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from .filters import AlumnoFilter, ProfesorFilter
from .models import Alumno, Profesor
from .serializers import AlumnoSerializer, ProfesorSerializer
from django_filters.rest_framework import DjangoFilterBackend

User = get_user_model()

class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        print(request.data)
        serializer = AlumnoSerializer(data=request.data)
        if serializer.is_valid():
            try:
                alumno = serializer.save()
                return Response({"message": "Usuario registrado exitosamente"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
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

#################APIS###########################3
class AlumnoAPI(generics.ListCreateAPIView):
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = AlumnoFilter

class ProfesorAPI(generics.ListCreateAPIView):
    queryset = Profesor.objects.all()
    serializer_class = ProfesorSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = ProfesorFilter
