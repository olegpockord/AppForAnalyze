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
def periodic_schedule_task():

    now = timezone.now()
    threshold = now - timedelta(days=3)
    three_days_date = threshold.date()

    queryset_of_articals = ArticalDate.objects.filter(date_of_last_update__lte=three_days_date)
    if not queryset_of_articals:
        return {'status': 'No articals available to update'}

    for article in queryset_of_articals:
        try:
            single_artical_update.delay(article.artice_id)
        except Exception as exc:
            LOG.exception(f"Failed to schedule update_single_article for {article.artice_id}: {exc}")

    LOG.info("Scheduled %d articles for update", len(queryset_of_articals))

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def single_artical_update(self, article_pk):

    lock_key = f'update_article_lock:{article_pk}'

    got_lock = cache.add(lock_key, '1', timeout=60 * 3)

    if not got_lock:
        LOG.info(f"Article {article_pk} is already being processed by another worker")
        return {'status': 'locked'}


    try:
        article = Artical.objects.get(pk=int(article_pk))
        doi = article.doi

        source = article.source

        if source == "openalex":
            url = f"https://api.openalex.org/works?filter=doi:{doi}"
            response = requests.get(url, timeout=10)
            data = response.json()["results"][0]

            cited_by_count = int(data.get("is-referenced-by-count"))
            reference_in_work = int(data.get("reference-count"))

            ArticalCiteData.objects.get(article=article).update(
                reference_count = cited_by_count,
                reference_in_work = reference_in_work,
            )

            ArticalDate.objects.get(article=article).update(
                date_of_last_update = timezone.now()
            )

            exist = {i.year: i
                     for i in ArticleCitePerYear.objects.filter(article=article)}
            to_update = []
            to_create = []
            
            citing_by_years = i.get("counts_by_year")

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
                ArticleCitePerYear.objects.bulk_update(to_update, ["citation"])


        elif source == "crossref":
            url = f"https://api.crossref.org/works/{doi}"
            response = requests.get(url, timeout=10)

            data = response.json()["message"]

            cited_by_count = int(data.get("is-referenced-by-count"))
            reference_in_work = int(data.get("reference-count"))

            ArticalCiteData.objects.get(article=article).update(
                reference_count = cited_by_count,
                reference_in_work = reference_in_work,
            )

            ArticalDate.objects.get(article=article).update(
                date_of_last_update = timezone.now()
            )

        cache.delete(lock_key)
        LOG.info(f"Updated article №{article_pk} (doi={doi})")
    except Exception as exc:
        LOG.exception(f"Network error while updating article {article_pk}")

        try:
            raise self.retry(exc=exc)
        except Exception:
            return {'status': 'error', 'error': str(exc)}
    finally:
        if got_lock:
            cache.delete(lock_key)

@shared_task
def dbackup_task():

    call_command('dbackup')