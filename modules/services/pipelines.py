from celery import chain

from modules.tasks import create_embedding, precompute_recommendations, create_search_vector

class ArticleAddingPipeline:

    @staticmethod
    def execute():
        chain(create_search_vector.s(), create_embedding.si(), precompute_recommendations.s()).apply_async()