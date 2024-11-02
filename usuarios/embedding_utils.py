
from sentence_transformers import SentenceTransformer
import re
import numpy as np


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

model = SentenceTransformer('hiiamsid/sentence_similarity_spanish_es')