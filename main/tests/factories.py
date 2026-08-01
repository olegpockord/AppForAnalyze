import factory
from datetime import datetime

from main.models import (
    Artical,
    ArticalCiteData,
    ArticalCiteInformation,
    ArticalDate,
    ArticalEmbedding,
    ArticleSearchVector,
    ArticleCitePerYear,
    ArticleMainAuthor,
    ArticleOtherAuthor,
)
from common.ml.sentence_transformer_model import get_model

from django.db.models import Value
from django.contrib.postgres.search import SearchVector

class ArticalFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Artical

    title = factory.Sequence(lambda n: f"Article №{n}")
    doi = factory.Sequence(lambda n: f"10.1000/st{n}")
    source = "openalex"

class ArticalCiteDataFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = ArticalCiteData

    article = factory.SubFactory(ArticalFactory)
    reference_count = factory.Sequence(lambda n: n)
    reference_in_work = factory.Sequence(lambda n: n)

class ArticalCiteInformationFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = ArticalCiteInformation

    article = factory.SubFactory(ArticalFactory)
    journal_name = factory.Sequence(lambda n: f"Journal №{n}")
    pages = factory.Sequence(lambda n: f"{n}-{n+1}")
    volume = factory.Sequence(lambda n: f"{200 + n}")
    issue = factory.Sequence(lambda n: f"{10 + n}")

class ArticalDateFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = ArticalDate
    
    article = factory.SubFactory(ArticalFactory)
    date_of_artical = factory.Sequence(lambda n: datetime(1900+n, 10, 10))

class ArticalEmbeddingFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = ArticalEmbedding

    article = factory.SubFactory(ArticalFactory)
    abstract_text = factory.Sequence(lambda n: f"This text num {n} contain some keywords: Django, space, programm, math")
    embedding = None

    class Params:

        encode = factory.Trait(
            embedding = factory.LazyAttribute(lambda obj: get_model().encode(obj.abstract_text, normalize_embeddings=True).tolist())
        )

class ArticleSearchVectorFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = ArticleSearchVector

    article = factory.SubFactory(ArticalFactory)
    search_vector = None

    @classmethod
    def generate_search_vector(cls, article):

        obj = cls(article=article)

        author = article.articlemainauthor_set.get()

        ArticleSearchVector.objects.filter(pk=obj.pk).update(
            search_vector = SearchVector(Value(article.title), weight='A')
                            + SearchVector(Value(author.main_initials), weight='B')
        )


class ArticleCitePerYearFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = ArticleCitePerYear

    article = factory.SubFactory(ArticalFactory)
    year = factory.Sequence(lambda n: n + 2010)
    citiation = factory.Sequence(lambda n: n)

class ArticleMainAuthorFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = ArticleMainAuthor

    article = factory.SubFactory(ArticalFactory)    
    main_initials = factory.Faker("name")

class ArticleOtherAuthorFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = ArticleOtherAuthor

    article = factory.SubFactory(ArticalFactory)    
    other_initials = factory.Faker("name")