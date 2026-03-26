from sentence_transformers import SentenceTransformer

# MODEL = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

model = None

def get_model():
    global model

    if not model:
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    return model
