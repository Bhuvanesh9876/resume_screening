import numpy as np

class VectorStore:
    def __init__(self, dimension):
        self.dimension = dimension

    def similarity(self, query_vec, doc_vec):
        return float(np.dot(query_vec, doc_vec))
