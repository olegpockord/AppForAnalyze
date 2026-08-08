from django.test import TestCase

from main.tests.factories import ArticalFactory
from modules.tasks import single_artical_update
from main.models import Artical

from unittest.mock import patch

class TestSingleUpdate(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.openalex = ArticalFactory() #source openalex by defaul
        cls.empty_source = ArticalFactory(source="")


    @patch("modules.tasks.cache.add", return_value=True)
    @patch("modules.tasks.cache.delete")
    @patch("modules.tasks.update_openalex_source", return_value={'status': "Succesful updated"})
    def test_normal_article(self, mock_update, mock_delete, mock_add):
        pk = self.openalex.pk

        result = single_artical_update.run(pk)

        mock_add.assert_called_once()

        mock_update.assert_called_once_with(Artical.objects.get(pk=pk))

        mock_delete.assert_called_once()

        self.assertEqual(result, {'status': "Succesful updated"})

    @patch("modules.tasks.cache.add", return_value=True)
    @patch("modules.tasks.cache.delete")
    def test_not_exist_article(self, mock_delete, mock_add):

        result = single_artical_update.run(999999)

        self.assertEqual(result, {'status': 'Error with article, it doesnot exist'})

    @patch("modules.tasks.cache.add", return_value=True)
    @patch("modules.tasks.cache.delete")
    def test_empty_source(self, mock_delete, mock_add):
        pk = self.empty_source.pk

        result = single_artical_update.run(pk)

        self.assertEqual(result, {'status': 'Error with source name'})

    @patch("modules.tasks.cache.add", return_value=False)
    @patch("modules.tasks.cache.delete")
    def test_cache_not_locked(self, mock_delete, mock_add):
        pk = self.openalex.pk

        result = single_artical_update.run(pk)

        mock_add.assert_called_once()
        mock_delete.assert_called_once()

        self.assertEqual(result, {'status': 'locked'})
        

