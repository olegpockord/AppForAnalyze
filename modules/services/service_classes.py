import logging

from modules.services.external_requests import APIFallbackResolver
from modules.services.parsers import OpenalexArticleParser, CrossrefArticleParser
from modules.services.crud_operations import ArticleUpdater
from modules.services.custom_exceptions import TooManyRequests, NetworkError

logger = logging.getLogger(__name__)

class ArticleImportService:
    
    def __init__(self):
        self.resolver = APIFallbackResolver()
        self.openalex_parser = OpenalexArticleParser()
        self.crossref_parser = CrossrefArticleParser()

    def import_article(self, query, identifier):

        parsers = {
            "openalex": self.openalex_parser,
            "crossref": self.crossref_parser
        }

        api, data = None, None

        try:
            api, data = self.resolver.fetch_search(query, identifier)
        except TooManyRequests:
            logger.warning(f"Couldnt import article, due to 429 response: query={query}; import={identifier}")
            return None
        except NetworkError:
            logger.warning(f"Some network error occured while import: query={query}; import={identifier}")

        parser = parsers.get(api)

        if not parser:
            logger.warning(f"Article import was unsuccessful: query={query}, identifier={identifier}")
            return None

        parsed_data = parser.parse_and_create(data)

        return parsed_data

class ArticleUpdateService:

    def __init__(self):
        self.resolver = APIFallbackResolver()
        self.updater = ArticleUpdater()
        self.openalex_parser = OpenalexArticleParser()
        self.crossref_parser = CrossrefArticleParser()

    def update(self, article):
        source = article.source
        logger.info(f"Article received for update: article_id={article.id}; source={source}; doi={article.doi}")

        data = None

        try:
            data = self.resolver.fetch_update(article)
        except TooManyRequests:
            logger.warning(f"Couldnt update article, due to 429 response: article_id={article.id}; source={source}; doi={article.doi}")
            return None
        except NetworkError:
            logger.warning(f"Some network error occured while update: article_id={article.id}; source={source}; doi={article.doi}")
            return None

        if not data:
            logger.warning(f"Resolver couldnt find info for article, it will be deleted: article_id={article.id}; source={source}; doi={article.doi}")
            return self.updater.delete_article(article)

        if source == "openalex":
            return self.update_openalex_article(article, data)

        if source == "crossref":
            return self.update_crossref_article(article, data)

    def update_openalex_article(self, article, json_data):
        citiation_data = self.openalex_parser.parse_citation(json_data)
        citiation_by_year_data = self.openalex_parser.parse_citation_by_year(json_data)

        self.updater.update_citations(article, citiation_data)
        self.updater.update_citations_by_year(article, citiation_by_year_data)
        self.updater.refresh_date_of_last_update(article)

        logger.info(f"Article was updated: article_id={article.id}; source={article.source}; doi={article.doi}")

    def update_crossref_article(self, article, json_data):
        citiation_data = self.crossref_parser.parse_citiation(json_data)

        self.updater.update_citations(article, citiation_data)
        self.updater.refresh_date_of_last_update(article)
        logger.info(f"Article was updated: article_id={article.id}; source={article.source}; doi={article.doi}")