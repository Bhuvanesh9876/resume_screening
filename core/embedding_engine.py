from sentence_transformers import SentenceTransformer
import streamlit as st
import numpy as np
from groq import Groq
from core.config import GROQ_API_KEY

DEFAULT_MODEL = "intfloat/e5-small-v2"

def normalize_vector(vec) -> np.ndarray:
    vec = np.array(vec, dtype=np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        return vec / norm
    return vec

@st.cache_resource
def load_model(model_name: str = DEFAULT_MODEL):
    return SentenceTransformer(model_name)

class EmbeddingEngine:

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model = load_model(model_name)
        self.client = None
        
        # Initialize Groq client if key is provided
        api_key = GROQ_API_KEY or st.secrets.get("GROQ_API_KEY")
        if api_key:
            try:
                self.client = Groq(api_key=api_key)
            except Exception:
                self.client = None

    def embed_resume(self, text: str) -> np.ndarray:
        if not text or not text.strip():
            return None
            
        text = text[:8000] if len(text) > 8000 else text
        
        # Try Groq for Llama-compatible/High-performance embeddings if available
        if self.client:
            try:
                # Using nomic-embed-text-v1.5 via Groq (standard high-perf embedding model)
                response = self.client.embeddings.create(
                    model="nomic-embed-text-v1.5",
                    input=text,
                    encoding_format="float"
                )
                embedding = np.array(response.data[0].embedding, dtype=np.float32)
                return normalize_vector(embedding)
            except Exception as e:
                # Soft fallback to local E5 if Groq fails or model is not available
                print(f"Groq Embedding Error: {e}")
                pass

        try:
            embedding = self.model.encode(
                f"passage: {text}",
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return normalize_vector(embedding)
        except Exception:
            return None

    def embed_query(self, text: str) -> np.ndarray:
        if not text or not text.strip():
            return None
            
        text = text[:4000] if len(text) > 4000 else text

        if self.client:
            try:
                response = self.client.embeddings.create(
                    model="nomic-embed-text-v1.5",
                    input=text,
                    encoding_format="float"
                )
                embedding = np.array(response.data[0].embedding, dtype=np.float32)
                return normalize_vector(embedding)
            except Exception:
                pass
        
        try:
            embedding = self.model.encode(
                f"query: {text}",
                normalize_embeddings=True,
                show_progress_bar=False
            )
            return normalize_vector(embedding)
        except Exception:
            return None

    @property
    def dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()
