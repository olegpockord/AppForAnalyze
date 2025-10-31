import requests
from datetime import datetime

from main.models import Artical, ArticalCiteData, ArticalDate, ArticalCiteInformation

from django.db import transaction
from django.core.cache import cache
from django.http import Http404

def fetch_openalex(doi):
    url = f"https://api.openalex.org/works?filter=doi:{doi}"
    r = requests.get(url, timeout=10)
    if r.status_code == 200 and len(r.json()["results"]) != 0:
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

    try:
        first_page = data["biblio"]["first_page"]
        last_page = data["biblio"]["last_page"]

        safety_data = get_safety_data_openalex(data)

        date_of_artical = datetime.strptime(data["publication_date"], "%Y-%m-%d").date()
        
        

        with transaction.atomic():
            
            artical = Artical.objects.create(
                title = data["title"],
                doi = (data["doi"][16::]).lower(),
                mag = safety_data["mag"],
                pubmed = safety_data["pubmed"][32::] if safety_data["pubmed"] else None,
                issn = safety_data["isbn"],
                isbn = safety_data["isbn"],
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
                volume = safety_data["volume"],
                author = data["authorships"][0]["raw_author_name"], # Придумать нормализацию в дальнейшем
                issue = data["biblio"]["issue"],
            )
    except Exception:
        raise Http404("При получении данных о статье возникла ошибка")
        

def parse_crossref(response):
    data = response.json()["message"]

    try:
        timestamp = int(data['created']['timestamp']) // 1000
        date_of_artical = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

        first_name = data["author"][0]["given"]
        last_name = data["author"][0]["family"]



        with transaction.atomic():
            artical = Artical.objects.create(
                title = data["title"][0],
                doi = (data["DOI"]).lower(),
                issn = data.get("ISSN")[0] if data.get("ISSN") else None,
                isbn = data.get("ISSN")[1] if data.get("ISSN") else None,
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
                volume = data.get("volume"),
                author = f"{last_name} {first_name}",
                issue = data["issue"],
            )
    except Exception:
        raise Http404("При получении данных о статье возникла ошибка")
        

def get_safety_data_openalex(response):
    ids = response.get("ids")

    mag = ids.get("mag")
    pmid = ids.get("pmid")

    issn_list = (response.get("primary_location", {}) .get("source", {}) .get("issn")) or []

    issn = issn_list[0] if len(issn_list) > 1 else None
    isbn = issn_list[1] if len(issn_list) > 1 else None

    volume = response.get("biblio").get("volume")

    return {
        "mag": mag,
        "pubmed": pmid,
        "issn": issn,
        "isbn": isbn,
        "volume": volume,
    }

    
    
