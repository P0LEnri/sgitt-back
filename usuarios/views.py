from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .filters import AlumnoFilter, ProfesorFilter
from .models import Alumno, Profesor, Materia
from .serializers import AlumnoSerializer, ProfesorSerializer, MateriaSerializer
from django_filters.rest_framework import DjangoFilterBackend
from .models import Alumno
from .serializers import AlumnoSerializer
from django.core.exceptions import ObjectDoesNotExist
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from rest_framework.decorators import api_view, permission_classes
#import spacy
from spellchecker import SpellChecker
#from gensim.models import KeyedVectors
import os
from transformers import AutoTokenizer, AutoModel
import torch
from django.core.cache import cache
from sentence_transformers import SentenceTransformer
from django.conf import settings
import logging
from django.db.models import Q
from django.http import Http404
import re
from typing import List, Tuple, Dict
import uuid
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from .embedding_utils import preprocess_text, model
from rest_framework import generics, status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Alumno, Profesor
from .serializers import AlumnoSerializer, ProfesorSerializer


# Cargar el modelo de spaCy para español
#nlp = spacy.load("es_core_news_sm")

# Inicializar el corrector ortográfico en español
#spell = SpellChecker(language='es')



User = get_user_model()

class RegisterUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = AlumnoSerializer(data=request.data)
        errors = {}

        # Validar si el correo ya existe
        email = request.data.get('email')
        if User.objects.filter(email=email).exists():
            errors['email'] = "Este correo electrónico ya está registrado."

        # Validar si la boleta ya existe
        boleta = request.data.get('boleta')
        if Alumno.objects.filter(boleta=boleta).exists():
            errors['boleta'] = "Esta boleta ya está registrada."

        # Validar contraseña
        password = request.data.get('password')
        if password:
            if len(password) < 8:
                errors['password'] = "La contraseña debe tener al menos 8 caracteres."
            elif not any(char.isdigit() for char in password):
                errors['password'] = "La contraseña debe contener al menos un número."
            elif not any(char.isupper() for char in password):
                errors['password'] = "La contraseña debe contener al menos una letra mayúscula."

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        if serializer.is_valid():
            try:
                alumno = serializer.save()
                return Response({
                    "message": "Usuario registrado exitosamente. Por favor, verifica tu correo electrónico."
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    "errors": {"general": str(e)}
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

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
                    'user_type': 'alumno' if hasattr(user, 'alumno') else 'profesor',
                    'user_email': str(email),
                    'primer_inicio': hasattr(user, 'profesor') and user.profesor.primer_inicio,
                    'is_admin': user.is_admin  # Añadir este campo
                })
            else:
                return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)
        except ObjectDoesNotExist:
            return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_admin(request):
    try:
        user = request.user
        print(f"Checking admin status for user: {user.email}")  # Debug log
        print(f"Is admin: {user.is_admin}")  # Debug log
        return Response({
            'is_admin': user.is_admin,
            'email': user.email
        })
    except Exception as e:
        print(f"Error checking admin status: {e}")  # Debug log
        return Response(
            {'error': 'Error checking admin status'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users(request):
    query = request.GET.get('q', '')
    logger.info(f"Searching users with query: {query}")
    
    if len(query) < 2:
        return Response([])
    
    User = get_user_model()
    
    # Log total users in database
    total_users = User.objects.count()
    logger.info(f"Total users in database: {total_users}")
    
    # Búsqueda en tabla de usuario base
    users = User.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).exclude(id=request.user.id)

    # Búsqueda por boleta (alumnos)
    alumnos_users = User.objects.filter(
        alumno__boleta__icontains=query
    ).exclude(id=request.user.id)

    # Búsqueda por apellido materno (alumnos y profesores)
    usuarios_materno = User.objects.filter(
        Q(alumno__apellido_materno__icontains=query) |
        Q(profesor__apellido_materno__icontains=query)
    ).exclude(id=request.user.id)

    # Combinar resultados
    users = users | alumnos_users | usuarios_materno
    users = users.distinct()  # Eliminar duplicados
    
    logger.info(f"Found {users.count()} users matching query")
    logger.info(f"Query results: {[user.email for user in users]}")
    
    results = []
    for user in users:
        user_data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'type': 'unknown'
        }

        try:
            if hasattr(user, 'alumno'):
                user_data.update({
                    'type': 'alumno',
                    'boleta': user.alumno.boleta,
                    'apellido_materno': user.alumno.apellido_materno,
                    'carrera': user.alumno.carrera
                })
            elif hasattr(user, 'profesor'):
                user_data.update({
                    'type': 'profesor',
                    'apellido_materno': user.profesor.apellido_materno,
                    'materias': [{'id': m.id, 'nombre': m.nombre} for m in user.profesor.materias.all()]
                })
        except Exception as e:
            logger.error(f"Error getting user details: {e}")

        results.append(user_data)

    return Response(results)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_users_data(request):
    User = get_user_model()
    
    data = {
        'total_users': User.objects.count(),
        'total_alumnos': Alumno.objects.count(),
        'total_profesores': Profesor.objects.count(),
        'sample_users': list(User.objects.values('id', 'email', 'first_name', 'last_name')[:5]),
        'sample_alumnos': list(Alumno.objects.values('user__email', 'boleta', 'apellido_materno')[:5]),
        'sample_profesores': list(Profesor.objects.values('user__email', 'matricula')[:5])
    }
    
    return Response(data)
 

def get_confidence_level(score: float) -> str:
    if score >= 0.7:
        return "Muy alta similitud"
    elif score >= 0.55:
        return "Alta similitud"
    elif score >= 0.35:
        return "Similitud moderada" 
    elif score >= 0.25:
        return "Baja similitud"
    else:
        return "Muy baja similitud"

def get_embeddings(texts: List[str]) -> np.ndarray:
    """
    Obtiene los embeddings para una lista de textos.
    """
    preprocessed_texts = [preprocess_text(text) for text in texts]
    return model.encode(preprocessed_texts)

def calculate_similarity_score(query_vector: np.ndarray, profesor: Profesor) -> Tuple[float, Dict]:
    """
    Calcula un puntaje de similitud compuesto para un profesor usando similitud coseno.
    Retorna el puntaje final y un diccionario con los puntajes individuales.
    """
    materias = list(profesor.materias.all())
    areas = list(profesor.areas_profesor.all())
    
    if not materias and not areas:
        return 0.0, {}
    
    # Calcular similitudes
    scores = {}
    
    if materias:
        materia_embeddings = [m.get_embedding_array() for m in materias]
        materia_embeddings = np.stack(materia_embeddings)
        # Normalizar los vectores
        materia_norms = np.linalg.norm(materia_embeddings, axis=1, keepdims=True)
        query_norm = np.linalg.norm(query_vector)
        # Calcular similitud coseno
        materia_similarities = np.dot(materia_embeddings, query_vector) / (materia_norms * query_norm)
        scores['max_materia'] = float(np.max(materia_similarities))
        scores['avg_materia'] = float(np.mean(materia_similarities))
    
    if areas:
        area_embeddings = [a.get_embedding_array() for a in areas]
        area_embeddings = np.stack(area_embeddings)
        # Normalizar los vectores
        area_norms = np.linalg.norm(area_embeddings, axis=1, keepdims=True)
        query_norm = np.linalg.norm(query_vector)
        # Calcular similitud coseno
        area_similarities = np.dot(area_embeddings, query_vector) / (area_norms * query_norm)
        scores['max_area'] = float(np.max(area_similarities))
        scores['avg_area'] = float(np.mean(area_similarities))
    
    # Calcular puntaje final ponderado
    final_score = 0.0
    if areas:
        weights = {
            'max_materia': 0.2,
            'avg_materia': 0.3,
            'max_area': 0.2,
            'avg_area': 0.3
        }
    else:
        weights = {
            'max_materia': 0.4,
            'avg_materia': 0.6
        }
    
    for key, weight in weights.items():
        if key in scores:
            final_score += scores[key] * weight
    confidence_level = get_confidence_level(final_score)
    
    return final_score, scores, confidence_level

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_profesores(request):
    """
    Endpoint para buscar profesores basado en similitud semántica.
    """
    query = request.GET.get('q', '').strip()
    debug_mode = request.GET.get('debug', '').lower() == 'true'
    
    try:
        # Si no hay query, devolver profesores recientes o destacados
        if not query:
            profesores = Profesor.objects.prefetch_related('materias', 'areas_profesor').all().order_by('-disponibilidad')[:10]
            serializer = ProfesorSerializer(profesores, many=True)
            return Response(serializer.data)

        # Preprocesar y obtener embedding de la consulta
        query_vector = get_embeddings([query])[0]
        
        # Obtener profesores con sus relaciones precargadas
        profesores = Profesor.objects.prefetch_related('materias', 'areas_profesor', 'user').all()
        
        # Calcular similitudes
        profesor_scores = []
        for profesor in profesores:
            final_score, detailed_scores,confidence_level  = calculate_similarity_score(query_vector, profesor)
            #print(f"Profesor: {profesor.user.email , profesor.user.id}, Score: {final_score:.3f} (Details: {detailed_scores})")
            
            if debug_mode:
                logger.info(f"Profesor: {profesor.user.email}")
                logger.info(f"Scores: {detailed_scores}")
                logger.info(f"Final Score: {final_score}")
           
            if final_score > 0.0:  # Umbral mínimo de similitud
                profesor_scores.append((profesor, final_score, detailed_scores,confidence_level))

            
        
        # Ordenar por puntaje y tomar los mejores resultados
        profesor_scores.sort(key=lambda x: (x[1], x[0].disponibilidad), reverse=True)
        top_profesores = profesor_scores[:18]
        
        # Preparar respuesta
        response_data = []
        for profesor, score, detailed_scores,confidence_level in top_profesores:
            profesor_data = ProfesorSerializer(profesor).data
            profesor_data['confidence'] = {
            'score': score,
            'level': confidence_level
        }
            print(f"Profesor: {profesor_data['email']}, Score: {score:.3f}, Confidence: {confidence_level}")
            if debug_mode:
                profesor_data['_debug'] = {
                    'similarity_score': score,
                    'detailed_scores': detailed_scores
                }
            response_data.append(profesor_data)
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error en búsqueda de profesores: {str(e)}", exc_info=True)
        return Response(
            {"error": "Error al procesar la búsqueda", "detail": str(e)},
            status=400
        )
def calculate_alumno_similarity_score(query_vector: np.ndarray, alumno: Alumno) -> Tuple[float, Dict, str]:
    """
    Calcula un puntaje de similitud compuesto para un alumno.
    Retorna el puntaje final, un diccionario con los puntajes individuales y el nivel de confianza.
    """
    areas = list(alumno.areas_alumno.all())
    
    if not areas:
        return 0.0, {}, "bajo"
    
    # Calcular similitudes
    scores = {}
    
    # Calcular similitudes de áreas
    area_embeddings = [a.get_embedding_array() for a in areas]
    area_embeddings = np.stack(area_embeddings)
    
    # Normalizar los vectores
    area_norms = np.linalg.norm(area_embeddings, axis=1, keepdims=True)
    query_norm = np.linalg.norm(query_vector)
    
    # Calcular similitud coseno
    area_similarities = np.dot(area_embeddings, query_vector) / (area_norms * query_norm)
    scores['max_area'] = float(np.max(area_similarities))
    scores['avg_area'] = float(np.mean(area_similarities))
    
    # Calcular puntaje final ponderado
    weights = {
        'max_area': 0.6,
        'avg_area': 0.4
    }
    
    final_score = sum(scores[key] * weight for key, weight in weights.items())
    
    # Determinar nivel de confianza
    confidence_level = get_confidence_level(final_score)
    
    return final_score, scores, confidence_level
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_alumnos(request):
    """
    Endpoint para buscar alumnos basado en similitud semántica.
    Solo accesible para profesores.
    """
    if not hasattr(request.user, 'profesor'):
        return Response(
            {"error": "Solo los profesores pueden buscar alumnos"},
            status=status.HTTP_403_FORBIDDEN
        )

    query = request.GET.get('q', '').strip()
    debug_mode = request.GET.get('debug', '').lower() == 'true'
    
    try:
        # Si no hay query, devolver alumnos recientes
        if not query:
            alumnos = Alumno.objects.prefetch_related('areas_alumno').all()[:18]
            serializer = AlumnoSerializer(alumnos, many=True)
            return Response(serializer.data)

        # Preprocesar y obtener embedding de la consulta
        query_vector = get_embeddings([query])[0]
        
        # Obtener alumnos con sus relaciones precargadas
        alumnos = Alumno.objects.prefetch_related('areas_alumno', 'user').all()
        
        # Calcular similitudes
        alumno_scores = []
        for alumno in alumnos:
            final_score, detailed_scores, confidence_level = calculate_alumno_similarity_score(query_vector, alumno)
            
            if debug_mode:
                logger.info(f"Alumno: {alumno.user.email}")
                logger.info(f"Scores: {detailed_scores}")
                logger.info(f"Final Score: {final_score}")
            
            if final_score > 0.0:  # Umbral mínimo de similitud
                alumno_scores.append((alumno, final_score, detailed_scores, confidence_level))
        
        # Ordenar por puntaje y tomar los mejores resultados
        alumno_scores.sort(key=lambda x: x[1], reverse=True)
        top_alumnos = alumno_scores[:18]
        
        # Preparar respuesta
        response_data = []
        for alumno, score, detailed_scores, confidence_level in top_alumnos:
            alumno_data = AlumnoSerializer(alumno).data
            alumno_data['confidence'] = {
                'score': score,
                'level': confidence_level
            }
            print(f"Alumno: {alumno_data['email']}, Score: {score:.3f}, Confidence: {confidence_level}")
            
            if debug_mode:
                alumno_data['_debug'] = {
                    'similarity_score': score,
                    'detailed_scores': detailed_scores
                }
            response_data.append(alumno_data)
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error en búsqueda de alumnos: {str(e)}", exc_info=True)
        return Response(
            {"error": "Error al procesar la búsqueda", "detail": str(e)},
            status=400
        )

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

class MateriasAPI(generics.ListAPIView):
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer

class MateriaViewSet(viewsets.ModelViewSet):
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer
    permission_classes = [AllowAny]

class AlumnoPerfilView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AlumnoSerializer

    def get_object(self):
        try:
            return Alumno.objects.get(user=self.request.user)
        except Alumno.DoesNotExist:
            raise Http404("No existe un perfil de alumno para este usuario")
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

class ProfesorPerfilView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfesorSerializer

    def get_object(self):
        try:
            return Profesor.objects.get(user=self.request.user)
        except Profesor.DoesNotExist:
            raise Http404("No existe un perfil de profesor para este usuario")
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    

class CambiarContrasenaProfesorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            profesor = Profesor.objects.get(user=request.user)
            if not profesor.es_profesor:
                return Response(
                    {"error": "Solo los profesores pueden usar esta función"},
                    status=status.HTTP_403_FORBIDDEN
                )

            password = request.data.get('password')
            confirm_password = request.data.get('confirmPassword')

            if not password or not confirm_password:
                return Response(
                    {"error": "Ambas contraseñas son requeridas"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if password != confirm_password:
                return Response(
                    {"error": "Las contraseñas no coinciden"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Actualizar contraseña y primer_inicio
            request.user.set_password(password)
            request.user.save()
            profesor.primer_inicio = False
            profesor.save()

            # Generar nuevos tokens
            refresh = RefreshToken.for_user(request.user)
            return Response({
                'message': 'Contraseña actualizada exitosamente',
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            })

        except Profesor.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class ResetPasswordRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            # Generar nuevo token
            user.verification_token = uuid.uuid4()
            user.save()
            
            # Enviar email
            reset_link = f"{settings.FRONTEND_URL}/reset-password/{user.verification_token}"
            send_mail(
                'Restablecer Contraseña',
                f'Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
                html_message=f'''
                <html>
                    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                            <h2 style="color: #4a5568;">Restablecer Contraseña</h2>
                            <p>Has solicitado restablecer tu contraseña. Haz clic en el siguiente botón para continuar:</p>
                            <a href="{reset_link}" style="display: inline-block; padding: 10px 20px; background-color: #4299e1; color: white; text-decoration: none; border-radius: 5px;">
                                Restablecer Contraseña
                            </a>
                            <p>Si no has solicitado restablecer tu contraseña, puedes ignorar este mensaje.</p>
                        </div>
                    </body>
                </html>
                '''
            )
            return Response(
                {"message": "Se ha enviado un enlace de restablecimiento a tu correo electrónico."},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"error": "No existe una cuenta con ese correo electrónico."},
                status=status.HTTP_404_NOT_FOUND
            )
class ResetPasswordConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, token):
        try:
            user = User.objects.get(verification_token=token)
            password = request.data.get('password')
            confirm_password = request.data.get('confirmPassword')

            if not password or not confirm_password:
                return Response(
                    {"error": "Ambas contraseñas son requeridas"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if password != confirm_password:
                return Response(
                    {"error": "Las contraseñas no coinciden"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if len(password) < 8:
                return Response(
                    {"error": "La contraseña debe tener al menos 8 caracteres"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not any(char.isdigit() for char in password):
                return Response(
                    {"error": "La contraseña debe contener al menos un número"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not any(char.isupper() for char in password):
                return Response(
                    {"error": "La contraseña debe contener al menos una letra mayúscula"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Actualizar contraseña
            user.set_password(password)
            user.verification_token = uuid.uuid4()  # Invalidar el token actual
            user.save()

            return Response(
                {"message": "Contraseña actualizada exitosamente"},
                status=status.HTTP_200_OK
            )

        except User.DoesNotExist:
            return Response(
                {"error": "Token inválido o expirado"},
                status=status.HTTP_400_BAD_REQUEST
            )
        

class CambiarContrasenaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            current_password = request.data.get('currentPassword')
            new_password = request.data.get('newPassword')
            confirm_password = request.data.get('confirmPassword')

            # Verificar que se proporcionaron todos los campos
            if not all([current_password, new_password, confirm_password]):
                return Response(
                    {"error": "Todos los campos son requeridos"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verificar que la contraseña actual es correcta
            if not user.check_password(current_password):
                return Response(
                    {"error": "La contraseña actual es incorrecta"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verificar que las contraseñas nuevas coinciden
            if new_password != confirm_password:
                return Response(
                    {"error": "Las contraseñas nuevas no coinciden"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validar que la nueva contraseña cumple con los requisitos
            try:
                # Validaciones personalizadas
                if len(new_password) < 8:
                    raise ValidationError(
                        "La contraseña debe tener al menos 8 caracteres."
                    )
                
                if not any(char.isdigit() for char in new_password):
                    raise ValidationError(
                        "La contraseña debe contener al menos un número."
                    )
                
                if not any(char.isupper() for char in new_password):
                    raise ValidationError(
                        "La contraseña debe contener al menos una letra mayúscula."
                    )

                # Validar la contraseña usando las validaciones de Django
                validate_password(new_password, user)

                # Verificar que la nueva contraseña no es igual a la actual
                if current_password == new_password:
                    return Response(
                        {"error": "La nueva contraseña debe ser diferente a la actual"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Actualizar la contraseña
                user.set_password(new_password)
                user.save()

                # Generar nuevos tokens para mantener la sesión activa
                from rest_framework_simplejwt.tokens import RefreshToken
                refresh = RefreshToken.for_user(user)

                return Response({
                    "message": "Contraseña actualizada exitosamente",
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                }, status=status.HTTP_200_OK)

            except ValidationError as e:
                return Response(
                    {"error": str(e).strip('[]').strip("'")},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {"error": "Ocurrió un error al cambiar la contraseña"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

            
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profesores(request):
    profesores = Profesor.objects.select_related('user').prefetch_related('materias', 'areas_profesor').all()
    serializer = ProfesorSerializer(profesores, many=True)
    return Response(serializer.data)
def get_alumnos(request):
    alumnos = Alumno.objects.select_related('user').all()
    serializer = AlumnoSerializer(alumnos, many=True)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profesor(request, pk):
    try:
        profesor = Profesor.objects.get(pk=pk)
        serializer = ProfesorSerializer(profesor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    except Profesor.DoesNotExist:
        return Response(status=404)
def update_alumno(request, pk):
    try:
        alumno = Alumno.objects.get(pk=pk)
        serializer = AlumnoSerializer(alumno, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    except Alumno.DoesNotExist:
        return Response(status=404)    

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_profesor(request, pk):
    try:
        profesor = Profesor.objects.get(pk=pk)
        profesor.delete()
        return Response(status=204)
    except Profesor.DoesNotExist:
        return Response(status=404)    
def delete_alumno(request, pk):
    try:
        alumno = Alumno.objects.get(pk=pk)
        alumno.delete()
        return Response(status=204)
    except Alumno.DoesNotExist:
        return Response(status=404)            
    

class AlumnoAPI(generics.ListCreateAPIView):
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Alumno.objects.select_related('user').all()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(boleta__icontains=search)
            )
        return queryset
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['include_user_id'] = True
        return context

class AlumnoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Extraer datos
        is_admin = request.data.get('is_admin')
        
        # Actualizar datos del usuario base
        user = instance.user
        user.email = request.data.get('email', user.email)
        user.first_name = request.data.get('nombre', user.first_name)
        user.last_name = request.data.get('apellido_paterno', user.last_name)
        
        # Actualizar is_admin explícitamente
        if is_admin is not None:
            user.is_admin = is_admin == 'true' or is_admin is True
        user.save()

        # Actualizar datos del alumno
        instance.apellido_materno = request.data.get('apellido_materno', instance.apellido_materno)
        instance.boleta = request.data.get('boleta', instance.boleta)
        instance.carrera = request.data.get('carrera', instance.carrera)
        instance.plan_estudios = request.data.get('plan_estudios', instance.plan_estudios)
        instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
class ProfesorAPI(generics.ListCreateAPIView):
    queryset = Profesor.objects.all()
    serializer_class = ProfesorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Profesor.objects.select_related('user').all()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(departamento__icontains=search)
            )
        return queryset

class ProfesorListView(generics.ListCreateAPIView):
    """Vista para listar y crear profesores (admin)"""
    queryset = Profesor.objects.select_related('user').prefetch_related('materias', 'areas_profesor')
    serializer_class = ProfesorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(departamento__icontains=search)
            )
        return queryset

class ProfesorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Vista para ver, actualizar y eliminar profesores (admin)"""
    queryset = Profesor.objects.select_related('user').prefetch_related('materias', 'areas_profesor')
    serializer_class = ProfesorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            # Crear usuario
            user = get_user_model().objects.create_user(
                email=data.get('email'),
                password=data.get('password', '123456'),  # Contraseña por defecto
                first_name=data.get('nombre'),
                last_name=data.get('apellido_paterno'),
                is_active=True,
                email_verified=True
            )

            # Crear profesor
            profesor = Profesor.objects.create(
                user=user,
                apellido_materno=data.get('apellido_materno'),
                departamento=data.get('departamento'),
                es_profesor=True,
                primer_inicio=True
            )

            serializer = self.get_serializer(profesor)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        try:
            serializer.save()
        except Exception as e:
            print(f"Error updating profesor: {str(e)}")
            raise

    def perform_destroy(self, instance):
        try:
            instance.user.delete()  # Esto también eliminará el profesor debido a la relación on_delete=CASCADE
        except Exception as e:
            print(f"Error deleting profesor: {str(e)}")
            raise
        
class AlumnoListView(generics.ListCreateAPIView):
    queryset = Alumno.objects.select_related('user').all()
    serializer_class = AlumnoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Alumno.objects.select_related('user').all()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(boleta__icontains=search)
            )
        return queryset        
        
    
# usuarios/views.py
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters import rest_framework as django_filters

class AlumnoFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='search_fields')
    carrera = django_filters.ChoiceFilter(choices=Alumno.Carrera.choices)
    plan_estudios = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Alumno
        fields = ['carrera', 'plan_estudios']

    def search_fields(self, queryset, name, value):
        return queryset.filter(
            Q(user__email__icontains=value) |
            Q(user__first_name__icontains=value) |
            Q(user__last_name__icontains=value) |
            Q(boleta__icontains=value)
        )

class ProfesorFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='search_fields')
    materias = django_filters.ModelMultipleChoiceFilter(
        queryset=Materia.objects.all(),
        field_name='materias',
        conjoined=False
    )

    class Meta:
        model = Profesor
        fields = ['materias']

    def search_fields(self, queryset, name, value):
        return queryset.filter(
            Q(user__email__icontains=value) |
            Q(user__first_name__icontains=value) |
            Q(user__last_name__icontains=value)
        )

class AlumnoViewSet(viewsets.ModelViewSet):
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = AlumnoFilter
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'boleta']
    
    

class ProfesorViewSet(viewsets.ModelViewSet):
    queryset = Profesor.objects.all()
    serializer_class = ProfesorSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ProfesorFilter
    search_fields = ['user__email', 'user__first_name', 'user__last_name']

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_problem(request):
    try:
        report_type = request.data.get('type')
        description = request.data.get('description')
        user_email = request.data.get('email')

        # Email content
        subject = f'Nuevo reporte de problema: {report_type}'
        message = f"""
        Tipo: {report_type}
        Descripcion: {description}
        Reportado por: {user_email}
        """
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.EMAIL_HOST_USER],
            fail_silently=False,
        )

        return Response({'message': 'Report sent successfully'})
    
    except Exception as e:
        return Response(
            {'message': 'Error sending report', 'error': str(e)}, 
            status=500
        )
# usuarios/views.py

# usuarios/views.py

class AlumnoListCreateView(generics.ListCreateAPIView):
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            
            # Procesar is_admin correctamente
            is_admin = data.get('is_admin')
            is_admin_bool = is_admin == 'true' or is_admin is True
            
            # Crear usuario
            user = User.objects.create_user(
                email=data['email'],
                password=data.get('password', '123456'),
                first_name=data['nombre'],
                last_name=data['apellido_paterno'],
                is_active=True,
                email_verified=True,
                is_admin=is_admin_bool  
            )

      
            alumno = Alumno.objects.create(
                user=user,
                apellido_materno=data['apellido_materno'],
                boleta=data['boleta'],
                carrera=data['carrera'],
                plan_estudios=data['plan_estudios']
            )

            serializer = self.get_serializer(alumno)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class ProfesorListCreateView(generics.ListCreateAPIView):
    queryset = Profesor.objects.all()
    serializer_class = ProfesorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            data = request.data
            
            # Crear usuario
            user = User.objects.create_user(
                email=data['email'],
                password=data.get('password', '123456'),
                first_name=data['nombre'],
                last_name=data['apellido_paterno'],
                is_active=True,
                email_verified=True,
                is_admin=data.get('is_admin', False)
            )

            # Crear profesor
            profesor = Profesor.objects.create(
                user=user,
                apellido_materno=data['apellido_materno'],
                departamento=data['departamento'],
                es_profesor=True,
                primer_inicio=True
            )
            
            if 'materias_ids' in data:
                materias_ids = data['materias_ids']
                profesor.materias.set(materias_ids)
        
            return Response(self.get_serializer(profesor).data, 
                       status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )