from django.utils import timezone
from django.core.cache import cache
from django.core.management import call_command
from django.db.models import F, Value
from django.contrib.postgres.search import SearchVector

from main.models import Artical, ArticalCiteData, ArticalDate, ArticleCitePerYear, ArticalEmbedding, ArticleSearchVector
from common.ml.sentence_transformer_model import get_model
from modules.services.recommendations import get_article_recommendations

import requests
from datetime import timedelta
from celery import shared_task
from celery.utils.log import get_task_logger, logging

logger = get_task_logger(__name__)
LOG = logging.getLogger(__name__)


@shared_task
def periodic_update_task():

    now = timezone.now()
    threshold = now - timedelta(days=3)
    three_days_date = threshold.date()

    queryset_of_articals = ArticalDate.objects.filter(date_of_last_update__lte=three_days_date)
    if not queryset_of_articals:
        return {'status': 'No articals available to update'}

    for i in queryset_of_articals:
        try:
            single_artical_update.delay(i.article.pk)
        except Exception as exc:
            LOG.exception(f"Failed to schedule update_single_article for {i.article.pk}: {exc}")

    LOG.info(f"Scheduled {len(queryset_of_articals)} articles for update")


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def single_artical_update(self, article_pk):
    lock_key = f'update_article_lock:{article_pk}'

    got_lock = cache.add(lock_key, '1', timeout=60 * 3)

    if not got_lock:
        LOG.info(f"Article {article_pk} is already being processed by another worker")
        return {'status': 'locked'}

    try:
        article = Artical.objects.get(pk=int(article_pk))

        source = article.source

        if source == "openalex":
            status = update_openalex_source(article)

        elif source == "crossref":
            status = update_crossref_source(article)

        else:
            LOG.exception(f"Error with source name occurred: {source} in article with №{article_pk}")
            return {'status': 'Error with source name'}
        
        return status or {'status': f'Not found status, smt was occured on article №{article_pk}'}
    
    except requests.RequestException as exc:
        raise self.retry(exc=exc)
    
    except Artical.DoesNotExist:
        LOG.exception(f"Article with pk - {article_pk} not found")
        return {'status': 'Error with article, it doesnot exist'}    
    
    except Exception:
        LOG.exception(f"Unexpected error was occurred: {Exception} while running article №{article_pk}")
        return {'status': 'Error while updating'}

    finally:
        cache.delete(lock_key)


@shared_task()
def create_embedding():
    embedding_set = ArticalEmbedding.objects.filter(embedding__isnull=True)
    
    if not embedding_set.exists():
        LOG.info("No articles available to set embedding")
        return None
    
    model = get_model()
    LOG.info(f"Device used - {model.device}")
    try:
        for obj in embedding_set:
            embedding = model.encode(obj.abstract_text, normalize_embeddings=True).tolist()

            ArticalEmbedding.objects.filter(pk=obj.pk).update(
                embedding=embedding,
            )
    except Exception as exc:
        LOG.exception(f"Failed to set embedding for {obj.article_id}: {exc}")

    LOG.info(f"Quantity of created embeddings: {len(embedding_set)}")

    ids_created_embedding = [object.article_id for object in embedding_set]

    return ids_created_embedding


@shared_task
def create_search_vector():
    qs = ArticleSearchVector.objects.filter(search_vector__isnull=True).annotate(
        title=F("article__title"),
        main_author=F("article__articlemainauthor__main_initials")
    )

    if not qs.exists():
        return {'status': 'No articles available to set search vector'}
    
    for obj in qs:
        ArticleSearchVector.objects.filter(pk=obj.pk).update(
            search_vector = SearchVector(Value(obj.title), weight='A')
                            + SearchVector(Value(obj.main_author), weight='B')
        )

    return {'status': f"Quantity of created search vectors: {len(qs)}"}


@shared_task()
def precompute_recommendations(ids_set):
    success = 0

    if not ids_set:
        return {'status': 'No articles avaible to precompute recomendations'}

    try:
        for id in ids_set:
            get_article_recommendations(id)
            success += 1

    except Exception as exc:
        LOG.exception(f"Failed to precompute recommendation for article №{id} due to {exc}")

    LOG.info(f"Quantity of precomputed recommendations: {len(ids_set)}, successful - {success}")

@shared_task
def dbackup_task():
    call_command('dbackup')



def update_openalex_source(article):
    doi = article.doi
    url = f"https://api.openalex.org/works?filter=doi:{doi}&select=ids,primary_location,referenced_works_count,cited_by_count,biblio,title,publication_date,counts_by_year,authorships&mailto=oleg222200005555@gmail.com"
    
    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.ConnectionError:
        LOG.info(f"Something with connection to API openalex")
        return {'status': "Error with connection to openalex"}

    data = response.json().get("results", [])

    if not data:
        return update_missing_doi_openalex(article)
    
    data = data[0]

    update_openalex_citing(data, article)
    refresh_date_of_last_update(article)

    update_openalex_citations_by_year(data, article)

    return {'status': 'article updated'}

def update_crossref_source(article):
    doi = article.doi
    url = f"https://api.crossref.org/works/{doi}"

    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.ConnectionError:
        LOG.info(f"Something with connection to API crossref")
        return {'status': "Error with connection to crossref"}
    
    data = response.json().get("message", [])

    if not data:
        return delete_article(article)
    

    update_crossref_citing(data, article)
    refresh_date_of_last_update(article)

    return {'status': f"article with doi: {doi} was updated"}

def update_missing_doi_openalex(article):
    mag = article.mag
    url = f"https://api.openalex.org/works?filter=mag:{mag}&select=ids,primary_location,referenced_works_count,cited_by_count,biblio,title,publication_date,counts_by_year,authorships&mailto=oleg222200005555@gmail.com"

    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.ConnectionError:
        LOG.info(f"Something with connection to API openalex")
        return {'status': "Error with connection to openalex"}
    
    data = response.json().get("results", [])

    if not data:
        return delete_article(article)
    
    data = data[0]

    update_openalex_citing(data, article)
    refresh_date_of_last_update(article)

    update_openalex_citations_by_year(data, article)

    return {'status': 'article was updated'}

    
def delete_article(article):

    try:
        article.delete()
    except Exception as exc:
        LOG.info(f"Article {article.title} with doi {article.doi} wasnt deleted due to {exc}")
        return {'status': f"Error with delete"}

    return {'status': f"Article {article.title} deleted"}


def refresh_date_of_last_update(article):

    ArticalDate.objects.filter(article=article).update(
            date_of_last_update = timezone.now()
    )


def update_openalex_citing(data, article):

    cited_by_count = int(data.get("cited_by_count"))
    reference_in_work = int(data.get("referenced_works_count"))

    ArticalCiteData.objects.filter(article=article).update(
        reference_count = cited_by_count,
        reference_in_work = reference_in_work,
    )


def update_openalex_citations_by_year(data, article):
    exist = {i.year: i
            for i in ArticleCitePerYear.objects.filter(article=article)}
    
    to_update = []
    to_create = []
            
    citing_by_years = data.get("counts_by_year")

    if citing_by_years:
        for i in citing_by_years:

            if i['year'] in exist:
                elem = exist[int(i['year'])]
                elem.citiation = int(i['cited_by_count'])
                to_update.append(elem)
            else:
                article_cite_per_year = ArticleCitePerYear(
                    article = article,
                    year = int(i['year']),
                    citiation = int(i['cited_by_count']),
                )
                to_create.append(article_cite_per_year)
                
        ArticleCitePerYear.objects.bulk_create(to_create)
        ArticleCitePerYear.objects.bulk_update(to_update, ["citiation"])


def update_crossref_citing(data, article):

    cited_by_count = int(data.get("is-referenced-by-count"))
    reference_in_work = int(data.get("reference-count"))

    ArticalCiteData.objects.filter(article=article).update(
    reference_count = cited_by_count,
    reference_in_work = reference_in_work,
    )


    



# @shared_task
# def periodic_schedule_task():

#     now = timezone.now()
#     threshold = now - timedelta(days=3)
#     three_days_date = threshold.date()

#     queryset_of_articals = ArticalDate.objects.filter(date_of_last_update__lte=three_days_date)
#     if not queryset_of_articals:
#         return {'status': 'No articals available to update'}

#     for i in queryset_of_articals:
#         try:
#             single_artical_update.delay(i.article.pk)
#         except Exception as exc:
#             LOG.exception(f"Failed to schedule update_single_article for {i.article.pk}: {exc}")

#     LOG.info("Scheduled %d articles for update", len(queryset_of_articals))

# @shared_task(bind=True, max_retries=3, default_retry_delay=30)
# def single_artical_update(self, article_pk):

#     lock_key = f'update_article_lock:{article_pk}'

#     got_lock = cache.add(lock_key, '1', timeout=60 * 3)

#     if not got_lock:
#         LOG.info(f"Article {article_pk} is already being processed by another worker")
#         return {'status': 'locked'}

#     print(f"{article_pk} - это айди для дои")
#     try:
#         article = Artical.objects.get(pk=int(article_pk))
#         doi = article.doi

#         source = article.source
#         # TODO made separate funtcitons to this
#         if source == "openalex":
#             url = f"https://api.openalex.org/works?filter=doi:{doi}&select=ids,primary_location,referenced_works_count,cited_by_count,biblio,title,publication_date,counts_by_year,authorships&mailto=oleg222200005555@gmail.com"
#             response = requests.get(url, timeout=10)
#             if len(response.json()["results"]) > 0:
#                 data = response.json()["results"][0]
#             else:
#                 LOG.info(f"Article with doi - {doi} is no longer in openalex, url swapped to mag search")
#                 mag = article.mag
#                 if mag:
#                     url = f"https://api.openalex.org/works?filter=mag:{mag}&select=ids,primary_location,referenced_works_count,cited_by_count,biblio,title,publication_date,counts_by_year,authorships&mailto=oleg222200005555@gmail.com"
#                     response = requests.get(url, timeout=10)
#                     if len(response.json()["results"]) > 0:
#                         data = response.json()["results"][0]
#                         Artical.objects.filter(mag=mag).update(
#                             doi = data.get("ids").get("doi")[16:].lower()
#                         )
#                     else:
#                         LOG.info(f"Article №{article_pk} with {doi}  was deleted")
#                         article.delete()
#                         cache.delete(lock_key)
#                         return {'status': 'No articals available to update'}
#                 else:
#                     LOG.info(f"Article №{article_pk} with {doi}  was deleted")
#                     article.delete()
#                     cache.delete(lock_key)
#                     return {'status': 'No articals available to update'}

#             cited_by_count = int(data.get("cited_by_count"))
#             reference_in_work = int(data.get("referenced_works_count"))

#             ArticalCiteData.objects.filter(article=article).update(
#                 reference_count = cited_by_count,
#                 reference_in_work = reference_in_work,
#             )

#             ArticalDate.objects.filter(article=article).update(
#                 date_of_last_update = timezone.now()
#             )

#             exist = {i.year: i
#                      for i in ArticleCitePerYear.objects.filter(article=article)}
#             to_update = []
#             to_create = []
            
#             citing_by_years = data.get("counts_by_year")

#             if citing_by_years:
#                 for i in citing_by_years:

#                     if i['year'] in exist:
#                         elem = exist[int(i['year'])]
#                         elem.citiation = int(i['cited_by_count'])
#                         to_update.append(elem)
#                     else:
#                         article_cite_per_year = ArticleCitePerYear(
#                             article = article,
#                             year = int(i['year']),
#                             citiation = int(i['cited_by_count']),
#                         )
#                         to_create.append(article_cite_per_year)
                
#                 ArticleCitePerYear.objects.bulk_create(to_create)
#                 ArticleCitePerYear.objects.bulk_update(to_update, ["citiation"])


#         elif source == "crossref":
#             url = f"https://api.crossref.org/works/{doi}"
#             response = requests.get(url, timeout=10)

#             data = response.json()["message"]

#             cited_by_count = int(data.get("is-referenced-by-count"))
#             reference_in_work = int(data.get("reference-count"))

#             ArticalCiteData.objects.get(article=article).update(
#                 reference_count = cited_by_count,
#                 reference_in_work = reference_in_work,
#             )

#             ArticalDate.objects.get(article=article).update(
#                 date_of_last_update = timezone.now()
#             )

#         cache.delete(lock_key)
#         LOG.info(f"Updated article №{article_pk} (doi={doi})")
#     except Exception as exc:
#         LOG.exception(f"Network error while updating article {article_pk}")

#         try:
#             raise self.retry(exc=exc)
#         except Exception:
#             return {'status': 'error', 'error': str(exc)}
#     finally:
#         if got_lock:
#             cache.delete(lock_key)