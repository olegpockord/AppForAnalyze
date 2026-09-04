from django.test import TestCase

from main.tests.factories import ArticalFactory

from modules.services.external_requests import BaseAPIRequest, OpenalexClient, CrossrefClient, APIFallbackResolver
from modules.services.custom_exceptions import TooManyRequests, NetworkError

from unittest.mock import patch, MagicMock, call
from requests import ConnectionError, Response


class TestCustomRequest(TestCase):
    url = "SomeUrl"
    source = "SomeSource"

    def setUp(self):
        self.request_call = BaseAPIRequest()

    @patch("modules.services.external_requests.requests.get")
    def test_normal_response(self, mock_get):
        mock_response = MagicMock()

        mock_response.status_code = 200
        mock_response.json.return_value = {"res": 1}

        mock_get.return_value = mock_response

        result = self.request_call.get_response(self.url, self.source)

        mock_get.assert_called_once()

        self.assertEqual(result, {"res": 1})

    @patch("modules.services.external_requests.logger")
    @patch("modules.services.external_requests.requests.get")
    def test_failure_connection(self, mock_get, mock_logger):
        mock_get.side_effect = ConnectionError()

        with self.assertRaises(NetworkError):
            self.request_call.get_response(self.url, self.source)

        mock_logger.warning.assert_called_once()

    @patch("modules.services.external_requests.requests.get")
    def test_429_response(self, mock_get):
        mock_get.return_value.status_code = 429

        with self.assertRaises(TooManyRequests):
            self.request_call.get_response(self.url, self.source)

    @patch("modules.services.external_requests.logger")
    @patch("modules.services.external_requests.requests.get")
    def test_bad_response(self, mock_get, mock_logger):
        # Status code could be 4xx or 5xx, request library catch that
        response = Response()
        response.status_code = 404

        mock_get.return_value = response

        with self.assertRaises(NetworkError):
            self.request_call.get_response(self.url, self.source)

        mock_logger.warning.assert_called_once()


class TestAPIClients(TestCase):
    query = "Django"
    doi = "10.1001/nt"

    @classmethod
    def setUpTestData(cls):
        cls.openalex = OpenalexClient()
        cls.crossref = CrossrefClient()

    @patch.object(BaseAPIRequest, "get_response")
    def test_normal_openalex_work(self, mock_request):
        mock_request.return_value = {"results": [231, 2]}

        result = self.openalex.fetch(self.query)

        mock_request.assert_called_once()

        self.assertEqual(result, [231, 2])

    @patch.object(BaseAPIRequest, "get_response")
    def test_crossref_no_info(self, mock_request):
        mock_request.return_value = {"message": []}

        result = self.crossref.fetch_by_doi(self.doi)

        self.assertIsNone(result)

class TestAPIFallback(TestCase):
    query = "SomeQuery"

    @classmethod
    def setUpTestData(cls):
        cls.default_article = ArticalFactory()
        cls.crossref_article = ArticalFactory(source="crossref")
        cls.article_witout_mag = ArticalFactory(mag=None)

    def setUp(self):
        self.fallback = APIFallbackResolver()

    # search fallback
    @patch("modules.services.external_requests.logger")
    @patch.object(OpenalexClient, "fetch")
    def test_openalex_return_data(self, mock_openalex, mock_logger):
        mock_openalex.return_value = ["someResults"]

        result = self.fallback.fetch_search(query=self.query, identifier="fts")

        self.assertEqual(result, ("openalex", ["someResults"]))

    @patch("modules.services.external_requests.logger")
    @patch.object(OpenalexClient, "fetch")
    @patch.object(CrossrefClient, "fetch_by_doi")
    def test_fallback_not_found_data(self, mock_crossref, mock_openalex, mock_logger):
        mock_openalex.return_value = None
        mock_crossref.return_value = None

        result = self.fallback.fetch_search(query=self.query, identifier="doi")

        mock_openalex.assert_called_once()
        mock_crossref.assert_called_once()
        mock_logger.warning.asssert_called_once()

        self.assertEqual(result, (None, None))

    @patch("modules.services.external_requests.logger")
    @patch.object(OpenalexClient, "fetch")
    @patch.object(CrossrefClient, "fetch_by_doi")
    def test_crossref_return_data(self, mock_crossref, mock_openalex, mock_logger):
        mock_openalex.return_value = None
        mock_crossref.return_value = ["someResults"]

        result = self.fallback.fetch_search(query=self.query, identifier="doi")

        mock_openalex.assert_called_once()

        self.assertEqual(result, ("crossref", ["someResults"]))

    # update_fallback
    @patch("modules.services.external_requests.logger")
    @patch.object(CrossrefClient, "fetch_by_doi")
    def test_crossref_found_data(self, mock_crossref, mock_logger):
        mock_crossref.return_value = ["someResults"]

        result = self.fallback.fetch_update(article_obj=self.crossref_article)

        self.assertEqual(result, ["someResults"])

    @patch("modules.services.external_requests.logger")
    @patch.object(OpenalexClient, "fetch")
    def test_openalex_mag_found_data(self, mock_openalex, mock_logger):
        doi_data = None
        mag_data = ["SomeResults"]

        mock_openalex.side_effect = [doi_data, mag_data]

        result = self.fallback.fetch_update(article_obj=self.default_article)

        self.assertEqual(result, mag_data)
        self.assertEqual(mock_openalex.call_args_list, [((self.default_article.doi,), {"identifier": "doi",}), call(self.default_article.mag, identifier="mag"),]) # We could use call() or do that in tuple, dict

    @patch("modules.services.external_requests.logger")
    @patch.object(OpenalexClient, "fetch")
    def test_data_not_found_without_mag(self, mock_openalex, mock_logger):
        mock_openalex.return_value = None

        result = self.fallback.fetch_update(article_obj=self.article_witout_mag)

        mock_logger.warning.assert_called_once()
        mock_openalex.assert_called_with(self.article_witout_mag.doi, identifier="doi")

        self.assertIsNone(result)