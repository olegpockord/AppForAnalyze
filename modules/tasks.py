from django.utils import timezone
from django.core.cache import cache
from django.core.management import call_command

from main.models import Artical, ArticalCiteData, ArticalDate

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
            single_artical_update.delay(article.artical_id)
        except Exception as exc:
            LOG.exception("Failed to schedule update_single_article for %s: %s", article.artical_id, exc)

    LOG.info("Scheduled %d articles for update", len(queryset_of_articals))

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def single_artical_update(self, artical_pk):

    lock_key = f'update_article_lock:{artical_pk}'

    got_lock = cache.add(lock_key, '1', timeout=60 * 3)

    # if not got_lock:
    #     LOG.info("Article %s is already being processed by another worker", artical_pk)
    #     return {'status': 'locked'}


    try:
        # artical = Artical.objects.get(pk=int(artical_pk))
        # doi = artical.doi
        

        # source = ArticalCiteData.objects.select_related("artical").get(artical_id = int(artical_pk)).source

        # if source == "openalex":
        #     url = f"https://api.openalex.org/works?filter=doi:{doi}"
        #     response = requests.get(url, timeout=10)
        #     data = response.json()["results"][0]

        #     reference_count = data["referenced_works_count"]
        #     reference_by_count = int(data["cited_by_count"])

        #     ArticalCiteData.objects.filter(artical=artical).update(
        #         raw = data,
        #         reference_count = reference_count,
        #         reference_by_count = reference_by_count,
        #     )

        #     ArticalDate.objects.update(
        #         date_of_last_update = timezone.now()
        #     )

        # elif source == "crossref":
        #     url = f"https://api.crossref.org/works/{doi}"
        #     response = requests.get(url, timeout=10)

        #     data = response.json()["message"]

        #     reference_count = int(data["reference-count"])
        #     reference_by_count = int(data["is-referenced-by-count"])

        #     ArticalCiteData.objects.filter(artical=artical).update(
        #         raw = data,
        #         reference_count = reference_count,
        #         reference_by_count = reference_by_count,
        #     )

        #     ArticalDate.objects.update(
        #         date_of_last_update = timezone.now()
        #     )

        cache.delete(lock_key)
        # LOG.info("Updated article %s (doi=%s)", artical_pk, doi)
    except Exception as exc:
        LOG.exception("Network error while updating article %s", artical_pk)

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