from django.core.cache import cache
from pgvector.django import CosineDistance
from common.ml.sentence_transformer_model import get_model

from main.models import Artical, ArticalEmbedding

def get_article_recommendations(article_id):
    cache_key = f"recommendation_№{article_id}"

    cached = cache.get(cache_key)

    if cached:
        qs = Artical.objects.filter(id__in = cached)
        return qs
    try:
        art = Artical.objects.get(id = article_id)
        abstract = art.abstract.first()

        if abstract and abstract.embedding is not None:
            qs = (
                ArticalEmbedding.objects.exclude(article__id = article_id)
                .annotate(distance=CosineDistance("embedding", abstract.embedding))
                .order_by("distance")[:3])
            
            ids = [i.article_id for i in qs]

            qs = Artical.objects.filter(id__in = ids)

        else:
            model = get_model()
            title_embedding = model.encode(art.title, device='cpu', normalize_embeddings=True).tolist()

            qs = (
                ArticalEmbedding.objects.annotate(distance=CosineDistance("embedding", title_embedding))
                .order_by("distance")[:3])
            
            # qs = (
            #     Artical.objects.exclude(id = article_id)
            #     .annotate(similarity=TrigramSimilarity("title", art.title))
            #     .order_by("-similarity")[:3])
            
            ids = [i.id for i in qs]

            qs = Artical.objects.filter(id__in = ids)
                

    except Artical.DoesNotExist:
        return []
    
    cache.set(cache_key, ids, 60 * 30)

    return qs    