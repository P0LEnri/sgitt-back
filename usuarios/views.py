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
from .embedding_utils import preprocess_text, model


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
                print('alumno' if hasattr(user, 'alumno') else 'profesor')
                print(str(email))
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user_type': 'alumno' if hasattr(user, 'alumno') else 'profesor',
                    'user_email': str(email),
                    'primer_inicio': hasattr(user, 'profesor') and user.profesor.primer_inicio
                })
            else:
                return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)
        except ObjectDoesNotExist:
            return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)
        

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
 


def get_embeddings(texts: List[str]) -> np.ndarray:
    """
    Obtiene los embeddings para una lista de textos.
    """
    preprocessed_texts = [preprocess_text(text) for text in texts]
    return model.encode(preprocessed_texts)

def calculate_similarity_score(query_vector: np.ndarray, profesor: Profesor) -> Tuple[float, Dict]:
    """
    Calcula un puntaje de similitud compuesto para un profesor.
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
        materia_similarities = np.dot(materia_embeddings, query_vector)
        scores['max_materia'] = float(np.max(materia_similarities))
        scores['avg_materia'] = float(np.mean(materia_similarities))
    
    if areas:
        area_embeddings = [a.get_embedding_array() for a in areas]
        area_embeddings = np.stack(area_embeddings)
        area_similarities = np.dot(area_embeddings, query_vector)
        scores['max_area'] = float(np.max(area_similarities))
        scores['avg_area'] = float(np.mean(area_similarities))
    
    # Calcular puntaje final ponderado
    final_score = 0.0
    if areas:
        weights = {
            'max_materia': 0.4,
            'avg_materia': 0.4,
            'max_area': 0.1,
            'avg_area': 0.1
        }
    else:
        weights = {
            'max_materia': 0.5,
            'avg_materia': 0.5
        }
    
    for key, weight in weights.items():
        if key in scores:
            final_score += scores[key] * weight
    
    return final_score, scores

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
            profesores = Profesor.objects.prefetch_related('materias', 'areas_profesor').all()[:10]
            serializer = ProfesorSerializer(profesores, many=True)
            return Response(serializer.data)

        # Preprocesar y obtener embedding de la consulta
        query_vector = get_embeddings([query])[0]
        
        # Obtener profesores con sus relaciones precargadas
        profesores = Profesor.objects.prefetch_related('materias', 'areas_profesor', 'user').all()
        
        # Calcular similitudes
        profesor_scores = []
        for profesor in profesores:
            final_score, detailed_scores = calculate_similarity_score(query_vector, profesor)
            print(f"Profesor: {profesor.user.email}, Score: {final_score:.3f} (Details: {detailed_scores})")

            if debug_mode:
                logger.info(f"Profesor: {profesor.user.email}")
                logger.info(f"Scores: {detailed_scores}")
                logger.info(f"Final Score: {final_score}")
            
            if final_score > 0.0:  # Umbral mínimo de similitud
                profesor_scores.append((profesor, final_score, detailed_scores))
        
        # Ordenar por puntaje y tomar los mejores resultados
        profesor_scores.sort(key=lambda x: x[1], reverse=True)
        top_profesores = profesor_scores[:6]
        
        # Preparar respuesta
        response_data = []
        for profesor, score, detailed_scores in top_profesores:
            profesor_data = ProfesorSerializer(profesor).data
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

class MateriaViewSet(viewsets.ReadOnlyModelViewSet):
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