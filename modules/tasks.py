from django.utils import timezone
from django.core.cache import cache
from django.core.management import call_command

from main.models import Artical, ArticalCiteData, ArticalDate, ArticleCitePerYear

import requests
from datetime import timedelta
from celery import shared_task
from celery.utils.log import get_task_logger, logging

logger = get_task_logger(__name__)
LOG = logging.getLogger(__name__)


@shared_task
def periodic_update_task():

    now = timezone.now()
    threshold = now - timedelta(days=2)
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

        if not article:
            LOG.exception(f"Article with pk - {article_pk} not found")
            return {'status': 'deleted'}

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
        return {'status': 'deleted'}    
    
    except Exception:
        LOG.exception(f"Unexpected error was occurred: {Exception} while running article №{article_pk}")
        return {'status': 'Error while updating'}

    finally:
        cache.delete(lock_key)


@shared_task
def dbackup_task():

    call_command('dbackup')



def update_openalex_source(article):
    doi = article.doi

    url = f"https://api.openalex.org/works?filter=doi:{doi}&select=ids,primary_location,referenced_works_count,cited_by_count,biblio,title,publication_date,counts_by_year,authorships&mailto=oleg222200005555@gmail.com"

    response = requests.get(url, timeout=10)
    data = response.json().get("results", [])

    if not data:
        return update_missing_doi_openalex(article)
    
    data = data[0]

    update_openalex_citing(data, article)
    refresh_date_of_last_update(article)

    update_openalex_citations_by_year(data, article)

    return {'status': 'article updated'}


def update_missing_doi_openalex(article):
    mag = article.mag

    url = f"https://api.openalex.org/works?filter=mag:{mag}&select=ids,primary_location,referenced_works_count,cited_by_count,biblio,title,publication_date,counts_by_year,authorships&mailto=oleg222200005555@gmail.com"

    response = requests.get(url, timeout=10)
    data = response.json().get("results", [])

    if not data:
        return delete_article(article)
    
    data = data[0]

    update_openalex_citing(data, article)
    refresh_date_of_last_update(article)

    update_openalex_citations_by_year(data, article)

    return {'status': 'article was updated'}


def update_crossref_source(article):
    doi = article.doi

    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url, timeout=10)
    data = response.json().get("message", [])

    if not data:
        return delete_article(article)
    

    update_crossref_citing(data, article)
    refresh_date_of_last_update(article)

    return {'status': 'article was updated'}

    
def delete_article(article):
    LOG.info(f"Article {article.title} with doi {article.doi} was deleted due to unavailable updating capability")
    article.delete()

    return {'status': 'deleted'}


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