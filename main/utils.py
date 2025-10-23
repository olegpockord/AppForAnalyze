import requests
from datetime import datetime

from main.models import Artical, ArticalCiteData, ArticalDate, ArticalCiteInformation
from django.db import transaction
from django.core.cache import cache

def fetch_openalex(doi):
    url = f"https://api.openalex.org/works?filter=doi:{doi}"
    r = requests.get(url, timeout=10)
    if r.status_code == 200 and len(r.json()["results"]) != 0:
        print("БЛЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯЯ")
        return parse_openalex(r)
    return fetch_crossref(doi)



def fetch_crossref(doi):
    url = f"https://api.crossref.org/works/{doi}"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        return parse_crossref(r)
    return None



def parse_openalex(response):

    data = response.json()["results"][0]

    first_page = data["biblio"]["first_page"]
    last_page = data["biblio"]["last_page"]

    date_of_artical = datetime.strptime(data["publication_date"], "%Y-%m-%d").date()
    
    pubmed = None

    try:
        pubmed = data["ids"]["pmid"][32::]
    except:
        KeyError

    with transaction.atomic():
        
        artical = Artical.objects.create(
            title = data["title"],
            doi = (data["doi"][16::]).lower(),
            mag = data["ids"]["mag"],
            pubmed = pubmed,
            issn = data["primary_location"]["source"]["issn"][0],
            isbn = data["primary_location"]["source"]["issn"][1] or None,
        )

        artical_cite_data = ArticalCiteData.objects.create(
            artical = artical,
            raw = data,
            reference_count = data["referenced_works_count"],
            reference_by_count = int(data["cited_by_count"]),
            source = "openalex",
        )

        artical_date = ArticalDate.objects.create(
            artical = artical,
            date_of_artical = date_of_artical,
        )

        artical_cite_information = ArticalCiteInformation.objects.create(
            artical = artical,
            journal_name = data["primary_location"]["source"]["display_name"],
            pages = f"{first_page}-{last_page}",
            volume = data["biblio"]["volume"],
            author = data["authorships"][0]["raw_author_name"], # Придумать нормализацию в дальнейшем
            issue = data["biblio"]["issue"],
        )
        

def parse_crossref(response):
    data = response.json()["message"]

    timestamp = int(data['created']['timestamp']) // 1000 # переделать
    date_of_artical = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

    first_name = data["author"][0]["given"]
    last_name = data["author"][0]["family"]

    isbn = None
    volume = None

    try:
        isbn = data["ISSN"][1]
        volume = data["volume"]
    except:
        IndexError or KeyError


    with transaction.atomic():
        artical = Artical.objects.create(
            title = data["title"][0],
            doi = (data["DOI"]).lower(),
            issn = data["ISSN"][0],
            isbn = isbn,
        )

        artical_cite_data = ArticalCiteData.objects.create(
            artical = artical,
            raw = data,
            reference_count = int(data["reference-count"]),
            reference_by_count = int(data["is-referenced-by-count"]),
            source = "crossref",
        )

        artical_date = ArticalDate.objects.create(
            artical = artical,
            date_of_artical = date_of_artical,
        )

        artical_cite_information = ArticalCiteInformation.objects.create(
            artical = artical,
            journal_name = data["container-title"][0],
            pages = data["page"],
            volume = volume,
            author = f"{last_name} {first_name}", # Придумать нормализацию в дальнейшем
            issue = data["issue"],
        )
        

def set_cache(cache_name, query, cache_time):
    data = cache.get(cache_name)

    if not data:
        data = query
        cache.set(cache_name, data, cache_time)

    return data



def get_data_for_cite():
    ...