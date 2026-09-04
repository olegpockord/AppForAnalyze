from django.test import TestCase
from django.utils import timezone

from main.tests.factories import ArticalFactory, ArticalDateFactory
from main.models import ArticalDate, Artical
from modules.tasks import periodic_update_task, single_artical_update
from modules.services.service_classes import ArticleUpdateService

from datetime import timedelta
from unittest.mock import patch

class TestPeriodicTask(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.old_default_article = ArticalFactory()
        cls.crossref_article = ArticalFactory(source="crossref")

        ArticalDateFactory(article = cls.old_default_article)
        ArticalDateFactory(article = cls.crossref_article)

    @patch("modules.tasks.LOG")
    @patch("modules.tasks.single_artical_update.delay")
    def test_old_articles(self, mock_delay, mock_logger):
        ArticalDate.objects.filter(article=self.old_default_article).update(
            date_of_last_update=timezone.now() - timedelta(days=4)
        )

        result = periodic_update_task()

        mock_delay.assert_called_once_with(self.old_default_article.pk)

        self.assertEqual(result, {'status': 'All articles in queue'})

    @patch("modules.tasks.single_artical_update.delay")
    def test_no_articles_to_update(self, mock_delay):
        result = periodic_update_task()

        mock_delay.assert_not_called()

        self.assertEqual(result, {'status': 'No articals available to update'})

    @patch("modules.tasks.LOG")
    @patch("modules.tasks.single_artical_update.delay")
    def test_after_exception(self, mock_delay, mock_logger):
        ArticalDate.objects.update(date_of_last_update=timezone.now() - timedelta(days=4))

        mock_delay.side_effect = [Exception("Some exception"), None]

        result = periodic_update_task()

        mock_logger.exception.assert_called_once()

        self.assertEqual(mock_delay.call_count, 2)
        self.assertEqual(result, {'status': 'All articles in queue'})


class TestSingleUpdate(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.default_article = ArticalFactory()
        cls.empty_source = ArticalFactory(source="")

    @patch("modules.tasks.cache.add", return_value=True)
    @patch("modules.tasks.cache.delete")
    @patch.object(ArticleUpdateService, "update")
    def test_normal_article(self, mock_update, mock_delete, mock_add):
        pk = self.default_article.pk

        single_artical_update.run(pk)

        mock_add.assert_called_once()
        mock_update.assert_called_once_with(Artical.objects.get(pk=pk))
        mock_delete.assert_called_once()

    @patch("modules.tasks.LOG")
    @patch("modules.tasks.cache.add", return_value=True)
    @patch("modules.tasks.cache.delete")
    def test_not_exist_article(self, mock_delete, mock_add, mock_logger):

        single_artical_update.run(999999)

        mock_logger.exception.assert_called_once()
        mock_delete.assert_called_once()

    @patch("modules.tasks.LOG")
    @patch("modules.tasks.cache.add", return_value=False)
    @patch("modules.tasks.cache.delete")
    def test_cache_not_locked(self, mock_delete, mock_add, mock_logger):
        pk = self.default_article.pk

        single_artical_update.run(pk)

        mock_add.assert_called_once()
        mock_logger.info.assert_called_once()
        mock_delete.assert_not_called()