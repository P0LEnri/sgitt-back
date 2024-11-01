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


# Cargar el modelo de spaCy para español
#nlp = spacy.load("es_core_news_sm")

# Inicializar el corrector ortográfico en español
#spell = SpellChecker(language='es')



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
                print('alumno' if hasattr(user, 'alumno') else 'profesor')
                print(str(email))
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user_type': 'alumno' if hasattr(user, 'alumno') else 'profesor',
                    'user_email': str(email)
                })
            else:
                return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)
        except ObjectDoesNotExist:
            return Response({"error": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)
        


""" 
            # Corrección ortográfica
            query_words = query.split()
            corrected_query = ' '.join([spell.correction(word) for word in query_words])

            # Lematización y eliminación de stopwords
            doc = nlp(corrected_query)
            lemmatized_query = ' '.join([token.lemma_ for token in doc if not token.is_stop])
            """


"""# Cargar el modelo de word embeddings (asegúrate de que la ruta sea correcta)
model_path = 'C:/Users/enri-/Downloads/cc.es.300.vec.gz'  # o .bin si usas el formato binario
word_vectors = KeyedVectors.load_word2vec_format(model_path, binary=False, limit=100000)  # Limita a 100,000 palabras para ahorrar memoria

def expand_query(query, word_vectors, topn=3):
    expanded_terms = []
    for word in query.split():
        try:
            similar_words = [w for w, _ in word_vectors.most_similar(word, topn=topn)]
            expanded_terms.extend(similar_words)
        except KeyError:
            # Si la palabra no está en el vocabulario, la ignoramos
            pass
    return ' '.join(set(query.split() + expanded_terms))

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_profesores(request):
    query = request.GET.get('q', '')
    profesores = list(Profesor.objects.all())

    if query and profesores:
        try:
            # Expandir la consulta con sinónimos
            expanded_query = expand_query(query, word_vectors)
            print(f"Consulta expandida: {expanded_query}")  # Para depuración
            corpus = [prof.materias for prof in profesores]
            #Expandir corpus con sinónimos
            corpus = [expand_query(materia, word_vectors) for materia in corpus]
            print(f"Corpus expandido: {corpus}")  # Para depuración

            vectorizer = TfidfVectorizer()
           
            tfidf_matrix = vectorizer.fit_transform(corpus)
            query_tfidf = vectorizer.transform([expanded_query])
            
            cosine_similarities = cosine_similarity(query_tfidf, tfidf_matrix).flatten()
            similar_indices = cosine_similarities.argsort()[::-1]
            
            # Seleccionar los 5 profesores más similares
            top_5_indices = similar_indices[:5]
            profesores = [profesores[int(i)] for i in top_5_indices ]
        except Exception as e:
            return Response({"error": str(e)}, status=400)
    
    serializer = ProfesorSerializer(profesores, many=True)
    return Response(serializer.data)"""

"""

# Cargar el modelo BETO
tokenizer = AutoTokenizer.from_pretrained("dccuchile/bert-base-spanish-wwm-uncased")
model = AutoModel.from_pretrained("dccuchile/bert-base-spanish-wwm-uncased")

def get_bert_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

def calculate_profesor_similarity(query_vector, profesor):
    
    #Calcula la similitud entre la consulta y cada materia del profesor,
    #devolviendo la máxima similitud encontrada.
    
    materias = profesor.materias.all()
    if not materias:
        return 0.0
    
    # Calcular similitud para cada materia
    materia_similarities = []
    for materia in materias:
        materia_vector = get_bert_embedding(materia.nombre)
        similarity = cosine_similarity([query_vector], [materia_vector])[0][0]
        materia_similarities.append(similarity)
    
    # Podemos usar diferentes estrategias para combinar las similitudes:
    # 1. Máximo (mejor coincidencia individual)
    max_similarity = max(materia_similarities)
    # 2. Promedio (coincidencia general)
    avg_similarity = sum(materia_similarities) / len(materia_similarities)
    # 3. Promedio ponderado de las mejores N coincidencias
    top_n = sorted(materia_similarities, reverse=True)[:2]  # Tomamos las 2 mejores
    weighted_similarity = sum(top_n) / len(top_n)
    
    # Combinamos las métricas (puedes ajustar los pesos según necesites)
    final_similarity = (max_similarity * 0.5 + 
                       avg_similarity * 0.2 + 
                       weighted_similarity * 0.3)
    
    return final_similarity

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_profesores(request):
    query = request.GET.get('q', '')
    # Obtener profesores con sus materias precargadas
    profesores = list(Profesor.objects.prefetch_related('materias').all())

    if query and profesores:
        try:
            print(f"Consulta: {query}")
            query_vector = get_bert_embedding(query)
            
            # Calcular similitudes
            similarities = []
            for prof in profesores:
                similarity = calculate_profesor_similarity(query_vector, prof)
                similarities.append((prof, similarity))
                print(f"Profesor: {prof.user.email}, Similitud: {similarity}")  # Debug

            # Filtrar y ordenar resultados
            filtered_similarities = [
                (prof, sim) for prof, sim in similarities 
                if sim > 0.3  # Umbral mínimo de similitud
            ]
            
            filtered_similarities.sort(key=lambda x: x[1], reverse=True)
            top_5_profesores = [prof for prof, sim in filtered_similarities[:6]]

            serializer = ProfesorSerializer(top_5_profesores, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            print(f"Error en búsqueda: {str(e)}")
            return Response({"error": str(e)}, status=400)
    
    # Si no hay query, devolver una selección limitada de profesores
    serializer = ProfesorSerializer(profesores[:9], many=True)
    return Response(serializer.data)

"""
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
 


"""

# Cargar el modelo una vez al inicio de la aplicación
model = SentenceTransformer('distiluse-base-multilingual-cased-v1') #hiiamsid/sentence_similarity_spanish_es

def get_embedding(text):
    return model.encode(text)

def get_profesor_similarities(query_vector, profesor):
    
    #Calcula la similitud entre la consulta y las materias del profesor
    
    materias = profesor.materias.all()
    if not materias:
        return 0.0

    # Obtener embeddings para cada materia
    materia_vectors = [get_embedding(materia.nombre) for materia in materias]
    
    # Calcular similitud con cada materia
    similitudes = [
        np.dot(query_vector, materia_vec) / (np.linalg.norm(query_vector) * np.linalg.norm(materia_vec))
        for materia_vec in materia_vectors
    ]
    
    # Podemos usar diferentes estrategias para combinar las similitudes:
    max_sim = max(similitudes)  # Mejor coincidencia
    avg_sim = sum(similitudes) / len(similitudes)  # Promedio
    
    # Combinar las métricas (ajustar pesos según necesidad)
    return max_sim * 0.99 + avg_sim * 0.01

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_profesores(request):
    query = request.GET.get('q', '')
    
    if not query:
        profesores = Profesor.objects.prefetch_related('materias').all()[:10]
        serializer = ProfesorSerializer(profesores, many=True)
        return Response(serializer.data)
    
    try:
        query_vector = get_embedding(query)
        
        # Intentar obtener profesores de la caché
        profesores = list(Profesor.objects.prefetch_related('materias').all())
        
        # Calcular similitudes para cada profesor
        similarities = []
        for profesor in profesores:
            similarity = get_profesor_similarities(query_vector, profesor)
            print(f"Profesor: {profesor.user.email}, Similitud: {similarity:.3f}")
            similarities.append((profesor, similarity))
        
        # Filtrar por umbral de similitud y ordenar
        filtered_similarities = [
            (prof, sim) for prof, sim in similarities 
            if sim > 0.4  # Ajustar umbral según necesidad
        ]
        
        # Ordenar por similitud y tomar los top 5
        top_profesores = sorted(filtered_similarities, key=lambda x: x[1], reverse=True)[:5]
        
        # Debug info
        for prof, sim in top_profesores:
            materias_nombres = ', '.join(m.nombre for m in prof.materias.all())
            print(f"Profesor: {prof.user.email}, Similitud: {sim:.3f}")
            print(f"Materias: {materias_nombres}")
        
        # Serializar resultados
        serializer = ProfesorSerializer([prof for prof, _ in top_profesores], many=True)
        return Response(serializer.data)
        
    except Exception as e:
        print(f"Error en búsqueda: {str(e)}")
        return Response({"error": str(e)}, status=400)

"""

# Inicializar el modelo una sola vez
model = SentenceTransformer('hiiamsid/sentence_similarity_spanish_es') #hiiamsid/sentence_similarity_spanish_es distiluse-base-multilingual-cased-v1

def preprocess_text(text: str) -> str:
    """
    Preprocesa el texto para mejorar la calidad de la búsqueda.
    """
    # Convertir a minúsculas y eliminar acentos
    text = text.lower()
    text = re.sub(r'[áäà]', 'a', text)
    text = re.sub(r'[éëè]', 'e', text)
    text = re.sub(r'[íïì]', 'i', text)
    text = re.sub(r'[óöò]', 'o', text)
    text = re.sub(r'[úüù]', 'u', text)
    
    # Eliminar caracteres especiales pero mantener espacios entre palabras
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    # Eliminar espacios múltiples
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

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

    # Obtener nombres de materias y áreas
    materia_texts = [m.nombre for m in materias]
    area_texts = [a.nombre for a in areas]
    
    # Calcular similitudes
    scores = {}
    
    if materia_texts:
        materia_vectors = get_embeddings(materia_texts)
        materia_similarities = cosine_similarity([query_vector], materia_vectors)[0]
        scores['max_materia'] = float(np.max(materia_similarities))
        scores['avg_materia'] = float(np.mean(materia_similarities))
    
    if area_texts:
        area_vectors = get_embeddings(area_texts)
        area_similarities = cosine_similarity([query_vector], area_vectors)[0]
        scores['max_area'] = float(np.max(area_similarities))
        scores['avg_area'] = float(np.mean(area_similarities))
    
    # Calcular puntaje final ponderado
    final_score = 0.0
    weights = {
        'max_materia': 0.4,
        'avg_materia': 0.4,
        'max_area': 0.1,
        'avg_area': 0.1
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
            #print(f"Profesor: {profesor.user.email}, Score: {final_score:.3f} (Details: {detailed_scores})")

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