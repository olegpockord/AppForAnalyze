import requests
from datetime import datetime

from main.models import Artical, ArticalCiteData, ArticalDate
from django.db import transaction


def fetch_openalex(doi):
    url = f"https://api.openalex.org/works?filter=doi:{doi}"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        return parse_openalex(r)
    return fetch_crossref(doi)



def fetch_crossref(doi):
    url = f"https://api.crossref.org/works/{doi}"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        return r.json()
    return None



def parse_openalex(response):
    data = response.json()["results"][0]
    print("кукукуку")


    with transaction.atomic():
        
        artical_cite_data = ArticalCiteData.objects.create(
            raw = data,
            reference_count = data["cited_by_count"],
            reference_by_count = int(data["referenced_works_count"]),
            source = "openalex"
        )

        artical_date = ArticalDate.objects.create(
            date_of_artical = datetime.strptime(data["publication_date"] , "%Y-%m-%d").date()
        )

        artical = Artical.objects.create(
            title = data["title"],
            doi = data["doi"][16::],
            mag = data["ids"]["mag"],
            pubmed = data["ids"]["pmid"][32::],
            issn = data["primary_location"]["source"]["issn"][0],
            isbn = data["primary_location"]["source"]["issn"][1],
            articalcite = artical_cite_data,
            articaldate = artical_date
        )