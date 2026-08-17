import requests

from modules.services.parsers import parse_openalex, parse_crossref

def fetch_openalex(filter_type, query, optional=''):
    url = f"https://api.openalex.org/works?{filter_type}{query}&select=ids,primary_location,referenced_works_count,cited_by_count,biblio,title,publication_date,abstract_inverted_index,counts_by_year,authorships{optional}&mailto=oleg222200005555@gmail.com"

    try:
        r = requests.get(url, timeout=7)
    except requests.exceptions.ConnectionError:
        return None

    if r.status_code == 200 and len(r.json()["results"]) != 0:
        return parse_openalex(r.json())
    elif r.status_code == 200 and filter_type == "filter=doi:":
        return fetch_crossref(query)
    else:
        return None
    
def fetch_crossref(doi):
    url = f"https://api.crossref.org/works/{doi}"
    try:
        r = requests.get(url, timeout=7)
    except requests.exceptions.ConnectionError:
        return None
    
    if r.status_code == 200:
        return parse_crossref(r.json())
    return None