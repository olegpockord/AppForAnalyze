from django.utils import timezone
from datetime import timedelta

from main.models import Artical, ArticalCiteData, ArticalCiteInformation, ArticalDate
from django.core.management import call_command

import requests
from celery import shared_task



def check_test_update(query):
    ...
    pk = query.pk
    doi = query.doi
    

    source = ArticalCiteData.objects.select_related("artical").get(artical_id = pk).source

    if source == "openalex":
        url = f"https://api.openalex.org/works?filter=doi:{doi}"
        response = requests.get(url, timeout=10)
        data = response.json()["results"][0]

        reference_count = data["referenced_works_count"]
        reference_by_count = int(data["cited_by_count"])

        ArticalCiteData.objects.update_or_create(
            artical = pk,
            raw = data,
            defaults={
                'reference_count': reference_count,
                'reference_by_count': reference_by_count
            }
        )

        ArticalDate.objects.update_or_create(artical=pk, date_of_last_update = timezone.now())

    else:
        url = f"https://api.crossref.org/works/{doi}"
        response = requests.get(url, timeout=10)

        data = response.json()["message"]

        reference_count = int(data["reference-count"])
        reference_by_count = int(data["is-referenced-by-count"])

        ArticalCiteData.objects.update_or_create(
            artical = pk,
            raw = data,
            defaults={
                'reference_count': reference_count,
                'reference_by_count': reference_by_count
            }
        )

        ArticalDate.objects.update_or_create(
            artical = pk,
            defaults= {'date_of_last_update': timezone.now()}
        )


    # now = timezone.now()
    # threshold = now - timedelta(days=3)
    # date1 = threshold.date()
    # # timezone.localtime() Это мое локально точное время

    # check_dates = ArticalDate.objects.filter(date_of_last_update__lte=date1)
    # for i in check_dates:
    #     print(i.date_of_last_update)


@shared_task
def dbackup_task():

    call_command('dbackup')