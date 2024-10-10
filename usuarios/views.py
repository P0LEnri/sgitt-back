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
from .models import Alumno
from .serializers import AlumnoSerializer
from django.core.exceptions import ObjectDoesNotExist


User = get_user_model()

class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = AlumnoSerializer(data=request.data)
        if serializer.is_valid():
            try:
                alumno = serializer.save()
                return Response({"message": "Usuario registrado exitosamente. Por favor, verifica tu correo electrónico."}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            user = User.objects.get(verification_token=token)
            if not user.email_verified:
                user.email_verified = True
                user.is_active = True
                user.save()
                return Response({"message": "Correo electrónico verificado exitosamente"}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "El correo electrónico ya ha sido verificado"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Token de verificación inválido"}, status=status.HTTP_400_BAD_REQUEST)




class LoginUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                if not user.is_active:
                    if not user.email_verified:
                        return Response({"error": "Por favor, verifica tu correo electrónico antes de iniciar sesión."}, status=status.HTTP_403_FORBIDDEN)
                    else:
                        return Response({"error": "Tu cuenta está inactiva. Contacta al administrador."}, status=status.HTTP_403_FORBIDDEN)
                
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user_type': 'alumno' if hasattr(user, 'alumno') else 'profesor'
                })
            else:
                return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)
        except ObjectDoesNotExist:
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
