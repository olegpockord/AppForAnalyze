from django.test import TestCase
from django.utils import timezone

from main.tests.factories import ArticalFactory, ArticalDateFactory, ArticalCiteDataFactory, ArticleCitePerYearFactory
from main.models import Artical, ArticalDate, ArticleCitePerYear
from modules.services.crud_operations import ArticleUpdater

from datetime import timedelta
from unittest.mock import patch


class TestDeleteOperations(TestCase):

    def setUp(self):
        self.default_article = ArticalFactory()
        self.updater = ArticleUpdater()

    def test_delete_normal(self):
        pk = self.default_article.pk

        result = self.updater.delete_article(self.default_article)

        self.assertIsNone(result)
        self.assertFalse(Artical.objects.filter(pk=pk).exists())

    @patch("modules.services.crud_operations.logger")
    @patch.object(Artical, "delete", side_effect = Exception("Some DB error"))
    def test_delete_error(self, mock_del, mock_logger):
        pk = self.default_article.pk

        self.updater.delete_article(self.default_article)

        mock_del.assert_called_once()
        mock_logger.warning.assert_called_once()

        self.assertTrue(Artical.objects.filter(pk=pk).exists())

class TestArticleUpdate(TestCase):

    def setUp(self):
        self.updater = ArticleUpdater()

    def test_article_refresh_date(self):
        old_article = ArticalFactory()
        old_date = (timezone.now() - timedelta(days=7)).date()

        article_date = ArticalDateFactory(
            article=old_article,
        )

        ArticalDate.objects.filter(pk=old_article.pk).update(
            date_of_last_update = old_date
        )

        self.updater.refresh_date_of_last_update(old_article)

        self.assertGreater(article_date.date_of_last_update, old_date)

    def test_citing_update(self):
        default_article = ArticalFactory()

        old_cite_data = ArticalCiteDataFactory(
            article = default_article,
            reference_count = 501,
            reference_in_work = 28
        )

        data = {
            "cited_by_count": 523,
            "reference_in_work": 29
        }

        self.updater.update_citations(default_article, data)

        old_cite_data.refresh_from_db()

        self.assertNotEqual(old_cite_data.reference_count, 501)
        self.assertNotEqual(old_cite_data.reference_in_work, 28)

        self.assertEqual(old_cite_data.reference_count, 523)
        self.assertEqual(old_cite_data.reference_in_work, 29)

    def test_update_citation_by_year(self):
        default_article = ArticalFactory()

        ArticleCitePerYearFactory(
            article = default_article,
            year = 2026,
            citiation = 51
        )

        data = {
            "citing_by_years": [
                {
                    "year": 2026,
                    "cited_by_count": 58
                }
            ]
        }
        
        self.updater.update_citations_by_year(default_article, data)
        citiation = ArticleCitePerYear.objects.get(article=default_article).citiation

        self.assertEqual(citiation, 58)

    def test_update_citations_new_year_add(self):
        default_article = ArticalFactory()

        ArticleCitePerYearFactory.create_batch(
            3,
            article = default_article
        )

        data = {
            "citing_by_years": [
                {
                    "year": 2026,
                    "cited_by_count": 2
                }
            ]
        }        

        self.updater.update_citations_by_year(default_article, data)

        quantity_of_records = ArticleCitePerYear.objects.filter(article=default_article).count()

        self.assertEqual(quantity_of_records, 4)