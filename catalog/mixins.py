from django.db.models import F
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
)
from django.contrib.postgres.search import SearchQuery, TrigramSimilarity
from pgvector.django import CosineDistance

from common.ml.sentence_transformer_model import get_model
from main.models import Artical, ArticleMainAuthor, ArticalEmbedding, ArticleSearchVector


class SearchMixin:

    search_methods = [
        "rank_search",
        "trigram_search",
        "embedding_search"
    ]

    def full_text_search(self, query):

        used_methods = [name for name in self.search_methods]

        # Trigram takes too much time for 2 or more words
        if len(query.split()) > 2: 
            used_methods.remove("trigram_search")
        
        for method_name in used_methods:
            method = getattr(self, method_name)

            ids = method(query)

            if ids:
                return ids

        return None

    
    def rank_search(self, query):
        search_query = SearchQuery(query)

        searchRank_ids = (ArticleSearchVector.objects
        .filter(search_vector=search_query)
        .annotate(similarity=SearchRank(F("search_vector"), search_query))
        .filter(similarity__gte=0.15)
        .values_list("article_id", flat=True))

        return searchRank_ids or []    


    # problem with pg_trgm constants: 0.3 for trigram_similar and 0.6 for trigram_word_similar. Need data for alter and choose method (1 or more word user typed for search)
    # Better test TrigramWordSimilarity (trigram_word_similar) for title
    def trigram_search(self, query):
        title_trgm = (Artical.objects.filter(title__trigram_similar=query)
        .annotate(similarity=TrigramSimilarity("title", query))
        .filter(similarity__gte=0.1)
        .values_list("id", flat=True))

        author_trgm = (ArticleMainAuthor.objects.filter(main_initials__trigram_similar=query)
        .annotate(similarity=TrigramSimilarity("main_initials", query))
        .filter(similarity__gte=0.15)
        .values_list("article_id", flat=True))

        trgm_ids = {*title_trgm, *author_trgm}

        return list(trgm_ids) or []

    def embedding_search(self, query):
        model = get_model()
        query_embedding = model.encode(query, normalize_embeddings=True).tolist()

        embedding_qs = (ArticalEmbedding.objects
        .exclude(embedding=None)
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[:300]
        ).values("article_id", "distance")

        filtered_ids_list = [obj["article_id"] for obj in embedding_qs if obj["distance"] < 0.4]

        return filtered_ids_list or []

    # def q_search(self, query, qs):
    #     raw_query = query

    #     vector = SearchVector("title", weight='A') + SearchVector("main_author_initials", weight='B')
    #     query = SearchQuery(query, search_type='phrase')
        
    #     searchRank_result = (
    #             qs.annotate(rank=SearchRank(vector, query))
    #             .filter(rank__gte=0.15)
    #         )

    #     if searchRank_result.exists():
    #         return searchRank_result
        
    #     trigram_result = qs.annotate(
    #         similarity_title = TrigramSimilarity('title', raw_query),
    #         similarity_author = TrigramSimilarity('main_author_initials', raw_query),
    #         similarity=Greatest('similarity_title', 'similarity_author')
    #         ).filter(similarity__gte=0.1)
        
    #     if trigram_result.exists():
    #         return trigram_result
        
    #     model = get_model()
    #     query_embedding = model.encode(raw_query, normalize_embeddings=True).tolist()

    #     return (qs.annotate(
    #         distance = CosineDistance('abstract__embedding', query_embedding))
    #         .exclude(abstract__embedding=None)
    #         .filter(distance__lt=0.6)
    #         )