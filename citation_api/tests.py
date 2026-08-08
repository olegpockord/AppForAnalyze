from django.test import TestCase
from rest_framework.test import APIClient

from main.tests.factories import ArticalFactory, ArticalCiteDataFactory, ArticalCiteInformationFactory, ArticleMainAuthorFactory, ArticalDateFactory


class TestCitiationAPI(TestCase):

    def setUp(self):
        self.article = ArticalFactory()
        self.client = APIClient()

    def test_api_normal_work(self):

        ArticalCiteDataFactory(article=self.article)
        ArticalCiteInformationFactory(article=self.article)
        ArticleMainAuthorFactory(article=self.article)
        ArticalDateFactory(article=self.article)

        response = self.client.get(
            f"/api/article/{self.article.pk}/citation/BibTex/"
        )

        self.assertEqual(response.status_code, 200)

    def test_api_not_found_id(self):

        response = self.client.get(
            f"/api/article/501/citation/BibTex/"
        )    

        self.assertEqual(response.status_code, 404)

    def test_api_wrong_citiation_type(self):

        response = self.client.get(
            f"/api/article/{self.article.pk}/citation/Bib/"
        )    

        self.assertIn("Supported formats:", response.content.decode())
        self.assertEqual(response.status_code, 404)        

    def test_api_rate_limit(self):

        ArticalCiteDataFactory(article=self.article)
        ArticalCiteInformationFactory(article=self.article)
        ArticleMainAuthorFactory(article=self.article)
        ArticalDateFactory(article=self.article)

        for _ in range(100):
            response = self.client.get(
                f"/api/article/{self.article.pk}/citation/BibTex/",
                REMOTE_ADDR=f"192.168.1.50",
            )   

            self.assertEqual(response.status_code, 200)

        response = self.client.get(
            f"/api/article/{self.article.pk}/citation/BibTex/",
            REMOTE_ADDR=f"192.168.1.50",
        )

        self.assertEqual(response.status_code, 429)
