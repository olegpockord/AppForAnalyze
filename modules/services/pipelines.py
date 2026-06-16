from celery import chain

from modules.tasks import create_embedding, precompute_recommendations

class ArticleAddingPipeline:

    @staticmethod
    def execute():
        chain(create_embedding.s(), precompute_recommendations.s()).apply_async()