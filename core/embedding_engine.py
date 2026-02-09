from sentence_transformers import SentenceTransformer

class EmbeddingEngine:
    def __init__(self, model_name="intfloat/e5-base"):
        self.model = SentenceTransformer(model_name)

    def embed_resume(self, text):
        return self.model.encode(
            f"passage: {text}", normalize_embeddings=True
        )

    def embed_query(self, text):
        return self.model.encode(
            f"query: {text}", normalize_embeddings=True
        )
