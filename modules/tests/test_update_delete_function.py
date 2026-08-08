from django.test import TestCase
from django.utils import timezone

from main.tests.factories import ArticalFactory, ArticalDateFactory, ArticalCiteDataFactory, ArticleCitePerYearFactory
from main.models import Artical, ArticalDate, ArticleCitePerYear
from modules.tasks import delete_article, refresh_date_of_last_update, update_openalex_citing, update_openalex_citations_by_year

from datetime import timedelta
from unittest.mock import patch

class TestArticleDelete(TestCase):

    def setUp(self):

        self.normal_article = ArticalFactory()


    def test_delete_normal(self):

        pk = self.normal_article.pk

        result = delete_article(self.normal_article)

        self.assertEqual(result, {'status': f"Article {self.normal_article.title} deleted"})

        self.assertFalse(Artical.objects.filter(pk=pk).exists())

    @patch.object(Artical, "delete", side_effect = Exception("Some DB error"))
    def test_delete_error(self, mock_del):

        result = delete_article(self.normal_article)

        mock_del.assert_called_once()

        self.assertEqual(result, {'status': "Error with delete"})

class TestArticleUpdate(TestCase):

    def test_article_refresh_date(self):

        old_article = ArticalFactory()
        old_date = (timezone.now() - timedelta(days=7)).date()

        article_date = ArticalDateFactory(
            article=old_article,
        )

        ArticalDate.objects.filter(pk=old_article.pk).update(
            date_of_last_update = old_date
        )

        refresh_date_of_last_update(old_article)

        self.assertGreater(article_date.date_of_last_update, old_date)

    def test_openalex_citing_update(self):

        openalex_article = ArticalFactory()

        old_cite_data = ArticalCiteDataFactory(
            article = openalex_article,
            reference_count = 501,
            reference_in_work = 28
        )

        data = {
            "cited_by_count": 523,
            "referenced_works_count": 29
        }

        update_openalex_citing(data, openalex_article)

        old_cite_data.refresh_from_db()

        self.assertNotEqual(old_cite_data.reference_count, 501)
        self.assertNotEqual(old_cite_data.reference_in_work, 28)

        self.assertEqual(old_cite_data.reference_count, 523)
        self.assertEqual(old_cite_data.reference_in_work, 29)

    def test_update_openalex_citations_old_var(self):

        openalex_article = ArticalFactory()

        ArticleCitePerYearFactory(
            article = openalex_article,
            year = 2026,
            citiation = 51
        )

        data = {
            "counts_by_year": [
                {
                    "year": 2026,
                    "cited_by_count": 58
                }
            ]
        }
        
        update_openalex_citations_by_year(data, openalex_article)

        citiation = ArticleCitePerYear.objects.get(article=openalex_article).citiation

        self.assertEqual(citiation, 58)

    def test_update_openalex_citations_new_year_add(self):

        openalex_article = ArticalFactory()

        ArticleCitePerYearFactory.create_batch(
            3,
            article = openalex_article
        )

        data = {
            "counts_by_year": [
                {
                    "year": 2026,
                    "cited_by_count": 2
                }
            ]
        }        

        update_openalex_citations_by_year(data, openalex_article)

        quantity_of_records = ArticleCitePerYear.objects.filter(article = openalex_article).count()

        self.assertEqual(quantity_of_records, 4)
