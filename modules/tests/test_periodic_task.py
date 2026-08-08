from django.test import TestCase
from django.utils import timezone

from main.tests.factories import ArticalFactory, ArticalDateFactory
from main.models import ArticalDate
from modules.tasks import periodic_update_task

from datetime import timedelta
from unittest.mock import patch

class TestPeriodicTask(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.openalex = ArticalFactory() #source openalex by default
        cls.crossref = ArticalFactory(source="crossref")


        ArticalDateFactory(
            article = cls.openalex,
        )

        ArticalDateFactory(
            article = cls.crossref,
        )


    @patch("modules.tasks.single_artical_update.delay")
    def test_old_articles(self, mock_delay):

        pk = self.openalex.pk

        ArticalDate.objects.filter(pk=pk).update(
            date_of_last_update=timezone.now() - timedelta(days=4)
        )

        result = periodic_update_task()

        mock_delay.assert_called_once_with(pk)

        self.assertEqual(result, {'status': 'Weekly update task ended'})


    @patch("modules.tasks.single_artical_update.delay")
    def test_no_articles_to_update(self, mock_delay):

        result = periodic_update_task()

        mock_delay.assert_not_called()

        self.assertEqual(result, {'status': 'No articals available to update'})

    @patch("modules.tasks.single_artical_update.delay")
    def test_after_exception(self, mock_delay):

        ArticalDate.objects.update(date_of_last_update=timezone.now() - timedelta(days=4))

        mock_delay.side_effect = Exception("Some exception")

        result = periodic_update_task()

        self.assertEqual(mock_delay.call_count, 2)

        self.assertEqual(result, {'status': 'Weekly update task ended'})

