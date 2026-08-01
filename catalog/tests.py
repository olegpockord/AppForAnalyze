from django.test import TestCase

from main.tests.factories import ArticalFactory, ArticalEmbeddingFactory, ArticleSearchVectorFactory, ArticleMainAuthorFactory
from catalog.mixins import SearchMixin

class TestSearchSystem(TestCase):

    @classmethod
    def setUpTestData(cls):
        
        cls.python = ArticalFactory(title = "Python ML libraries")
        cls.django = ArticalFactory(title = "Django for beginers")
        cls.math = ArticalFactory(title = "Math in algorithms")
        cls.numpy = ArticalFactory(title="Array programming with Numpy")

        ArticalEmbeddingFactory(
            article = cls.python,
            abstract_text = "Python has decent amount libraries for ML",
            encode=True
        )

        ArticalEmbeddingFactory(
            article = cls.django,
            abstract_text = "With Django you could easily run your first web app",
            encode=True
        )

        ArticalEmbeddingFactory(
            article = cls.math,
            abstract_text = "Fast algorithms requires math calculations",
            encode=True
        )        

        ArticleMainAuthorFactory(
            article = cls.python,
            main_initials = "John D."
        )

        ArticleMainAuthorFactory(
            article = cls.django,
            main_initials = "Bob Hunter"
        )

        ArticleMainAuthorFactory(
            article = cls.math,
            main_initials = "Alexander Dirak"
        )

        ArticleSearchVectorFactory(
            article = cls.python
        )

        ArticleSearchVectorFactory.generate_search_vector(cls.python)

        ArticleSearchVectorFactory(
            article = cls.django
        )

        ArticleSearchVectorFactory.generate_search_vector(cls.django)

        ArticleSearchVectorFactory(
            article = cls.math
        )

        ArticleSearchVectorFactory.generate_search_vector(cls.math)

# Search rank
    def test_search_rank_finds(self):

        id = list(SearchMixin().rank_search("Math"))

        self.assertIn(self.math.pk, id)

    def test_search_rank_return_empty(self):

        id = SearchMixin().rank_search("Foreign")

        self.assertEqual([], id)

    def test_search_rank_finds_author(self):

        id = SearchMixin().rank_search("Hunter")

        self.assertIn(self.django.pk, id)

# Trigram search
    def test_trigram_finds_key_word_with_mistake(self):
        # Bad test for now
        id = SearchMixin().trigram_search("Array nump")

        self.assertIn(self.numpy.pk, id)

    def test_trigram_finds_author_with_mistake(self):
    
        id = SearchMixin().trigram_search("Alexader")
    
        self.assertIn(self.math.pk, id)

    def test_trigram_return_empty(self):

        id = SearchMixin().trigram_search("Djng")

        self.assertEqual([], id)

# Embedding search
    def test_embedding_search_finds(self):

        id = SearchMixin().embedding_search("Python libraries")

        self.assertIn(self.python.pk, id)

    def test_embedding_search_finds_meaning(self):

        id = SearchMixin().embedding_search("Математические вычисления") # Math calculations in russian
        
        self.assertIn(self.math.pk, id)

    def test_embedding_search_return_empty(self):

        id = SearchMixin().embedding_search("Programming language")

        self.assertEqual([], id)