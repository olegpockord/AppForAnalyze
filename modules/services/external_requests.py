import requests
import logging

from AppForAnalyze.settings import API_KEY
from modules.services.custom_exceptions import TooManyRequests, NetworkError

logger = logging.getLogger(__name__)

api_key = API_KEY

if api_key:
    api_key=f"&api_key={api_key}"

class BaseAPIRequest:

    def get_response(self, url, source, timeout=7):
        try:
            response = requests.get(url, timeout=7)

            if response.status_code == 429:
                raise TooManyRequests

            response.raise_for_status()            
        except requests.RequestException as exc:
            logger.warning(f"{source} request failed: exc={exc}")
            raise NetworkError

        return response.json()        

class OpenalexClient:

    def __init__(self):
        self.custom_request = BaseAPIRequest()

    FILTERS = {
        "doi": "filter=doi:",
        "mag": "filter=mag:",
        "pmid": "filter=pmid:",
        "fts": "search="
    }

    def fetch(self, query, identifier="fts"):
        filter_type = self.FILTERS[identifier]

        optional = ''

        if identifier == "fts":
            optional = "&per-page=50"

        url = f"https://api.openalex.org/works?{filter_type}{query}&select=ids,primary_location,referenced_works_count,cited_by_count,biblio,title,publication_date,abstract_inverted_index,counts_by_year,authorships{optional}{api_key}&mailto=oleg222200005555@gmail.com"

        response = self.custom_request.get_response(url, source="Openalex")

        return response["results"] if response.get("results") else None

class CrossrefClient:

    def __init__(self):
        self.custom_request = BaseAPIRequest()
        
    def fetch_by_doi(self, doi):
        url = f"https://api.crossref.org/works/{doi}"

        response = self.custom_request.get_response(url, source="Crossref")

        return response["message"] if response.get("message") else None


class APIFallbackResolver:

    def __init__(self):
        self.openalex = OpenalexClient()
        self.crossref = CrossrefClient()

    def fetch_search(self, query, identifier):
        openalex_data = self.openalex.fetch(query, identifier)

        if openalex_data:
            logger.info(f"Search complete succesfully: api=openalex; identifier={identifier}")
            return "openalex", openalex_data

        if identifier == "doi":
            crossref_data = self.crossref.fetch_by_doi(query)

            if crossref_data:
                logger.info(f"Search fallback by doi worked: api=crossref; identifier={identifier}")
                return "crossref", crossref_data

        logger.warning(f"Fallback for search couldnt find any data: query={query}; identifier={identifier}")
        return None, None

    def fetch_update(self, article_obj):
        doi = article_obj.doi

        if article_obj.source == "crossref":
            crossref_data = self.crossref.fetch_by_doi(doi)
            return crossref_data

        data = self.openalex.fetch(doi, identifier="doi")

        if data:
            logger.info(f"Openalex article by doi received: article_id={article_obj.id}; doi={doi}")
            return data

        if article_obj.mag:
            data = self.openalex.fetch(article_obj.mag, identifier="mag")

        if data:
            logger.info(f"Openalex article by mag received: article_id={article_obj.id}; doi={doi}; mag={article_obj.mag}")
            return data

        logger.warning(f"Fallback for update couldnt find any data: article_id={article_obj.id}; doi={doi}; mag={article_obj.mag}")

        return None