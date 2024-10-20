from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated
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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from rest_framework.decorators import api_view, permission_classes
import spacy
from spellchecker import SpellChecker
from gensim.models import KeyedVectors
import os
from transformers import AutoTokenizer, AutoModel
import torch
from django.core.cache import cache
from sentence_transformers import SentenceTransformer
from django.conf import settings

# Cargar el modelo de spaCy para español
nlp = spacy.load("es_core_news_sm")

# Inicializar el corrector ortográfico en español
spell = SpellChecker(language='es')



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




# Cargar el modelo BETO
tokenizer = AutoTokenizer.from_pretrained("dccuchile/bert-base-spanish-wwm-uncased")
model = AutoModel.from_pretrained("dccuchile/bert-base-spanish-wwm-uncased")

def get_bert_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_profesores(request):
    query = request.GET.get('q', '')
    profesores = list(Profesor.objects.all())

    if query and profesores:
        try:
            print(f"Consulta: {query}")  # Para depuración
            query_vector = get_bert_embedding(query)
            
            similarities = []
            for prof in profesores:
                prof_vector = get_bert_embedding(prof.materias)
                similarity = cosine_similarity([query_vector], [prof_vector])[0][0]
                similarities.append((prof, similarity))

            similarities.sort(key=lambda x: x[1], reverse=True)
            print(similarities)
            top_5_profesores = [prof for prof, _ in similarities[:5]]
            #imprimir similitudes
            print(top_5_profesores)
            serializer = ProfesorSerializer(top_5_profesores, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=400)
    
    serializer = ProfesorSerializer(profesores, many=True)
    return Response(serializer.data)


 

"""


# Cargar el modelo una vez al inicio de la aplicación
model = SentenceTransformer('hiiamsid/sentence_similarity_spanish_es')

def get_embedding(text):
    return model.encode(text)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_profesores(request):
    query = request.GET.get('q', '')
    
    if not query:
        profesores = Profesor.objects.all()[:10]  # Limitar a 10 si no hay consulta
        serializer = ProfesorSerializer(profesores, many=True)
        return Response(serializer.data)
    
    try:
        query_vector = get_embedding(query)
        
        # Intentar obtener embeddings precalculados de la caché
        profesores_embeddings = cache.get('profesores_embeddings')
        if profesores_embeddings is None:
            profesores = list(Profesor.objects.all())
            profesores_embeddings = [(prof, get_embedding(prof.materias)) for prof in profesores]
            cache.set('profesores_embeddings', profesores_embeddings, timeout=settings.CACHE_TIMEOUT)
        
        # Calcular similitudes
        similarities = [
            (prof, np.dot(query_vector, prof_vector) / (np.linalg.norm(query_vector) * np.linalg.norm(prof_vector)))
            for prof, prof_vector in profesores_embeddings
        ]
        #print(similarities)
        # Filtrar similitudes mayores a 0
        filtered_similarities = [(prof, sim) for prof, sim in similarities if sim > 0.6 ]

        # Ordenar y seleccionar los 5 más similares
        top_5_profesores = sorted(filtered_similarities, key=lambda x: x[1], reverse=True)[:5]
        print(top_5_profesores)

        # Serializar
        serializer = ProfesorSerializer([prof for prof, _ in top_5_profesores], many=True)

        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=400)



"""

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
