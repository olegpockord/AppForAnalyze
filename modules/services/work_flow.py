from celery import chain
import logging

from modules.tasks import create_embedding, precompute_recommendations, create_search_vector
from modules.services.service_classes import ArticleImportService

logger = logging.getLogger(__name__)

class ArticleImportWorkFlow:
    def __init__(self):
        self.service = ArticleImportService()

    def post_adding(self):
        chain(create_search_vector.s(), create_embedding.si(), precompute_recommendations.s()).apply_async()

    def execute_import(self, query, identifier):
        logger.info(f"Starts article import: query={query}, identifier={identifier}")

        import_result = self.service.import_article(query, identifier)

        if import_result:
            logger.info(f"Succesfully complete import: returned value={import_result}")
            self.post_adding()
            return import_result

        return None
            