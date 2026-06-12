from django.core.cache import cache
from pgvector.django import CosineDistance
from common.ml.sentence_transformer_model import get_model
from django.db.models.expressions import ExpressionWrapper
from django.db.models import F, IntegerField, Value

from main.models import Artical, ArticalEmbedding

def get_article_recommendations(article_id):
    # cache_key = f"recommendation_№{article_id}"

    # cached = cache.get(cache_key)

    # if cached:
    #     qs = Artical.objects.filter(id__in = cached)
    #     return qs
    try:
        art = Artical.objects.get(id = article_id)
        abstract = art.abstract.first()

        if abstract and abstract.embedding is not None:
            qs = (
                ArticalEmbedding.objects.exclude(article__id = article_id)
                .annotate(distance=CosineDistance("embedding", abstract.embedding))
                .annotate(similarity=ExpressionWrapper((Value(1) - F("distance")) * 100, output_field=IntegerField()))
                .annotate(
                    date=F("article__articaldate__date_of_artical"),
                    citations_in_article=F("article__articalcitedata__reference_count"),
                    main_author=F("article__articlemainauthor__main_initials"),
                    journal_name=F("article__articalciteinformation__journal_name"),
                    article_title=F("article__title"),
                    article_pk=F("article__id")
                )
                .order_by("distance")[:3])

        else:
            model = get_model()
            title_embedding = model.encode(art.title, device='cpu', normalize_embeddings=True).tolist()

            qs = (
                ArticalEmbedding.objects.exclude(article__id = article_id)
                .annotate(distance=CosineDistance("embedding", title_embedding))
                .annotate(similarity=ExpressionWrapper((Value(1) - F("distance")) * 100, output_field=IntegerField()))
                .annotate(
                    date=F("article__articaldate__date_of_artical"),
                    citations_in_article=F("article__articalcitedata__reference_count"),
                    main_author=F("article__articlemainauthor__main_initials"),
                    article_title=F("article__title"),
                    article_pk=F("article__id")
                )
                .order_by("distance")[:3])
                
    except Artical.DoesNotExist:
        return []
    
    # cache.set(cache_key, ids, 60 * 30)

    return qs    