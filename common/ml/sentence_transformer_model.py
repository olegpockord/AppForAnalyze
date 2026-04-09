from sentence_transformers import SentenceTransformer
from sentence_transformers.models import Transformer, Pooling
from AppForAnalyze.settings import MODEL_PATH
# MODEL = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

model = None

def get_model():
    global model

    if model:
        return model

    if not MODEL_PATH.exists():
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cpu')
    else:
        transformer = Transformer(MODEL_PATH)
        word_embedding_dim = transformer.get_word_embedding_dimension()
        pooling = Pooling(word_embedding_dim)
        model = SentenceTransformer(modules=[transformer, pooling], device='cpu')

    return model
