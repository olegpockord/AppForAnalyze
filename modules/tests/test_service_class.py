from django.test import TestCase

from modules.services.service_classes import ArticleUpdateService, ArticleImportService
from modules.services.external_requests import APIFallbackResolver
from main.tests.factories import ArticalFactory
from modules.services.custom_exceptions import TooManyRequests, NetworkError

from unittest.mock import patch, Mock

class TestUpdateService(TestCase):

    def setUp(self):
        self.service = ArticleUpdateService()
        self.default_article = ArticalFactory()
        self.crossref_article = ArticalFactory(source="crossref")

    @patch("modules.services.service_classes.logger")
    @patch.object(ArticleUpdateService, "update_openalex_article")
    def test_normal_openalex_update(self, mock_update, mock_logger):
        raw_json = {"results": "SomeJsonData"}

        self.service.resolver.fetch_update = Mock(return_value=raw_json)
        self.service.update(self.default_article)

        mock_update.assert_called_once()
        mock_update.assert_called_once_with(self.default_article, raw_json)

    @patch("modules.services.service_classes.logger")
    @patch.object(ArticleUpdateService, "update_crossref_article")
    def test_normal_crossref_update(self, mock_update, mock_logger):
        raw_json = {"message": "SomeJsonData"}

        self.service.resolver.fetch_update = Mock(return_value=raw_json)
        self.service.update(self.crossref_article)

        mock_update.assert_called_once()
        mock_update.assert_called_once_with(self.crossref_article, raw_json)

    @patch("modules.services.service_classes.logger")
    def test_article_not_found(self, mock_logger):
        self.service.updater.delete_article = Mock()

        self.service.resolver.fetch_update = Mock(return_value=None)
        self.service.update(self.default_article)

        self.service.updater.delete_article.assert_called_once()
        mock_logger.warning.assert_called_once()

    @patch("modules.services.service_classes.logger")
    def test_raised_429(self, mock_logger):
        self.service.resolver.fetch_update = Mock(side_effect=TooManyRequests)

        result = self.service.update(self.default_article)

        mock_logger.warning.assert_called_once()
        self.assertIsNone(result)

    @patch("modules.services.service_classes.logger")
    def test_raised_network_error(self, mock_logger):
        self.service.resolver.fetch_update = Mock(side_effect=NetworkError)

        result = self.service.update(self.default_article)

        mock_logger.warning.assert_called_once()
        self.assertIsNone(result)

    @patch("modules.services.service_classes.logger")
    def test_update_openalex_article(self, mock_logger):
        raw_json = {"results": "SomeJsonData"}

        citiation_data = {
            "cited_by_count": 523,
            "reference_in_work": 29
        }

        citiation_data_by_year = {
            "citing_by_years": [
                {
                    "year": 2026,
                    "cited_by_count": 58
                }
            ]
        }

        self.service.openalex_parser.parse_citation = Mock(return_value=citiation_data)
        self.service.openalex_parser.parse_citation_by_year = Mock(return_value=citiation_data_by_year)

        self.service.updater.update_citations = Mock()
        self.service.updater.update_citations_by_year = Mock()
        self.service.updater.refresh_date_of_last_update = Mock()

        self.service.update_openalex_article(self.default_article, raw_json)

        self.service.updater.update_citations.assert_called_once_with(self.default_article, citiation_data)
        self.service.updater.update_citations_by_year.assert_called_once_with(self.default_article, citiation_data_by_year)
        self.service.updater.refresh_date_of_last_update.assert_called_once_with(self.default_article)

class TestImportService(TestCase):

    def setUp(self):
        self.service = ArticleImportService()

    @patch.object(APIFallbackResolver, "fetch_search")
    def test_successful_import(self, mock_fallback):
        raw_json = {"results": "SomeJsonData"}
        doi = ["10.1001/nt"]

        mock_fallback.return_value = ("openalex", raw_json)
        self.service.openalex_parser.parse_and_create = Mock(return_value=doi)
        self.service.crossref_parser.parse_and_create = Mock()

        result = self.service.import_article("SomeQuery", "fts")

        self.service.openalex_parser.parse_and_create.assert_called_once_with(raw_json)
        self.service.crossref_parser.parse_and_create.assert_not_called()

        self.assertEqual(result, doi)

    @patch("modules.services.service_classes.logger")
    @patch.object(APIFallbackResolver, "fetch_search")
    def test_unsuccessful_import(self, mock_fallback, mock_logger):
        mock_fallback.return_value = (None, None)

        result = self.service.import_article("SomeQuery", "fts")

        mock_logger.warning.assert_called_once()
        self.assertIsNone(result)

    @patch("modules.services.service_classes.logger")
    @patch.object(APIFallbackResolver, "fetch_search")
    def test_429_while_import(self, mock_fallback, mock_logger):
        mock_fallback.side_effect = TooManyRequests

        result = self.service.import_article("SomeQuery", "fts")

        mock_logger.warning.assert_called_once()
        self.assertIsNone(result)

    @patch("modules.services.service_classes.logger")
    @patch.object(APIFallbackResolver, "fetch_search")
    def test_network_error_while_import(self, mock_fallback, mock_logger):
        mock_fallback.side_effect = NetworkError

        result = self.service.import_article("SomeQuery", "fts")

        self.assertEqual(mock_logger.warning.call_count, 2)
        self.assertIsNone(result)