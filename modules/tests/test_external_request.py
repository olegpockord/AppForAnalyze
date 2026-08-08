from django.test import TestCase

from main.tests.factories import ArticalFactory
from modules.tasks import update_openalex_source, update_missing_doi_openalex, update_crossref_source
from modules.services.external_requests import fetch_openalex, fetch_crossref

from unittest.mock import patch, MagicMock
from requests import ConnectionError


class TestOpenalexCallFunctions(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.default_article = ArticalFactory()

    # Tests for update articles
    @patch("modules.tasks.update_openalex_citations_by_year")
    @patch("modules.tasks.refresh_date_of_last_update")
    @patch("modules.tasks.update_openalex_citing")
    @patch("modules.tasks.requests.get")
    def test_openalex_update_by_doi(self, mock_get, mock_update_citing, mock_refresh, mock_update_citations):

        mock_response = MagicMock()

        mock_response.json.return_value = {
            "results": [
                {
                    "cited_by_count": 301,
                    "referenced_works_count": 27
                }
            ]
        }

        mock_get.return_value = mock_response

        result = update_openalex_source(self.default_article)

        mock_update_citing.assert_called_once_with({"cited_by_count": 301, "referenced_works_count": 27}, self.default_article)
        mock_refresh.assert_called_once()
        mock_update_citations.assert_called_once_with({"cited_by_count": 301, "referenced_works_count": 27}, self.default_article)

        self.assertEqual(result, {'status': f"openalex article with doi: {self.default_article.doi} was updated"})

    @patch("modules.tasks.update_missing_doi_openalex")
    @patch("modules.tasks.requests.get")
    def test_openalex_update_by_boi_miss_data(self, mock_get, mock_missing):
        article = self.default_article

        mock_response = MagicMock()

        mock_response.json.return_value = {
            "status": "Not found"
        }

        mock_get.return_value = mock_response
        mock_missing.return_value = {'status': f'openalex article {article.title} with missing doi (by mag) was updated'}

        result = update_openalex_source(article)

        mock_missing.assert_called_once_with(article)

        self.assertEqual(result, {'status': f'openalex article {article.title} with missing doi (by mag) was updated'})

    @patch("modules.tasks.requests.get")
    def test_openalex_update_connection_error(self, mock_get):

        mock_get.side_effect = ConnectionError()

        result = update_openalex_source(self.default_article)

        self.assertEqual(result, {'status': "Error with connection to openalex"})

    @patch("modules.tasks.delete_article")
    @patch("modules.tasks.requests.get")
    def test_openalex_update_by_mag_not_found(self, mock_get, mock_delete):
        article = self.default_article

        mock_response = MagicMock()

        mock_response.json.return_value = {
            "status": "not found"
        }

        mock_get.return_value = mock_response

        mock_delete.return_value = {'status': f"Article {article.title} deleted"}

        result = update_missing_doi_openalex(article)

        mock_delete.assert_called_once_with(article)

        self.assertEqual(result, {'status': f"Article {article.title} deleted"})

    # Tests for calling parser

    @patch("modules.services.external_requests.parse_open_alex")
    @patch("modules.services.external_requests.requests.get")
    def test_fetch_openalex_fts(self, mock_get, mock_parse):

        mock_response = MagicMock()

        mock_response.json.return_value = {
            "results": [
                {
                    "cited_by_count": 301,
                    "referenced_works_count": 27
                }
            ]
        }

        mock_response.status_code = 200

        mock_get.return_value = mock_response
        mock_parse.return_value = ["10.1001/nt", "10.1000/ht"]

        filter_type = "search="
        query = "Unit+testing"
        optional = "&per-page=50"

        result = fetch_openalex(filter_type, query, optional)

        mock_parse.assert_called_once_with(mock_response.json.return_value)

        self.assertEqual(result, ["10.1001/nt", "10.1000/ht"])

    @patch("modules.services.external_requests.requests.get")
    def test_fetch_openalex_by_mag_return_empty(self, mock_get):

        mock_response = MagicMock()

        mock_response.json.return_value = {
            "results": []
        }        

        mock_response.status_code = 200

        mock_get.return_value = mock_response

        filter_type = "filter=mag:"
        query = "Django"

        result = fetch_openalex(filter_type, query)

        self.assertEqual(result, None)

    @patch("modules.services.external_requests.fetch_crossref")
    @patch("modules.services.external_requests.requests.get")
    def test_fetch_openalex_call_crossref(self, mock_get, mock_fetch):

        mock_response = MagicMock()

        mock_response.json.return_value = {
            "results": []
        }

        mock_response.status_code = 200

        mock_get.return_value = mock_response
        mock_fetch.return_value = ["10.1000/ht"]

        filter_type = "filter=doi:"
        query = "Api+requests"

        result = fetch_openalex(filter_type, query)

        mock_fetch.assert_called_once_with(query)

        self.assertEqual(result, ["10.1000/ht"])

        
class TestCrossrefCallFunctions(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.default_article = ArticalFactory(source="crossref")

    # Tests for update articles
    @patch("modules.tasks.refresh_date_of_last_update")
    @patch("modules.tasks.update_crossref_citing")
    @patch("modules.tasks.requests.get")
    def test_crossref_update_normal(self, mock_get, mock_update, mock_refresh):
        article = self.default_article

        mock_response = MagicMock()

        mock_response.json.return_value = {
            "message": {
                "indexed": {},
                "issue": "7822"
            }
        }

        mock_response.status_code = 200

        mock_get.return_value = mock_response

        result = update_crossref_source(article)

        mock_update.assert_called_once_with({"indexed": {}, "issue": "7822"}, article)
        mock_refresh.assert_called_once_with(article)
        
        self.assertEqual(result, {'status': f"crossref article with doi: {article.doi} was updated"})

    @patch("modules.tasks.delete_article")
    @patch("modules.tasks.requests.get")
    def test_crossref_update_return_404(self, mock_get, mock_delete):
        article = self.default_article

        mock_response = MagicMock()

        mock_response.status_code = 404

        mock_get.return_value = mock_response

        mock_delete.return_value = {'status': f"Article {article.title} deleted"}

        result = update_crossref_source(article)

        mock_delete.assert_called_once_with(article)

        self.assertEqual(result, {'status': f"Article {article.title} deleted"})

    # Tests for calling parser

    @patch("modules.services.external_requests.parse_crossref")
    @patch("modules.services.external_requests.requests.get")
    def test_crossref_fetch_normal(self, mock_get, mock_parse):
        article = self.default_article

        mock_response = MagicMock()

        mock_response.json.return_value = {
            "status": "ok",
            "message": [
                {}
            ]
        }

        mock_response.status_code = 200

        mock_get.return_value = mock_response
        mock_parse.return_value = article.doi

        result = fetch_crossref(article.doi)

        mock_parse.assert_called_once_with(mock_response.json.return_value)

        self.assertEqual(result, article.doi)

    @patch("modules.services.external_requests.requests.get")
    def test_crossref_fetch_return_404(self, mock_get):

        mock_response = MagicMock()

        mock_response.status_code = 404

        mock_get.return_value = mock_response

        result = fetch_crossref(self.default_article.doi)

        self.assertEqual(result, None)


