import requests
import time
from modules.services.parsers import parse_open_alex, parse_crossref

def fetch_openalex(type, query, optional):
    url = f"https://api.openalex.org/works?{type}{query}&select=ids,primary_location,referenced_works_count,cited_by_count,biblio,title,publication_date,abstract_inverted_index,counts_by_year,authorships{optional}&mailto=oleg222200005555@gmail.com"
    start = time.time()
    try:
        r = requests.get(url, timeout=20)
    except requests.exceptions.ConnectionError:
        return None
    print(f"Время в мс {(time.time() - start) * 1000}")
    if r.status_code == 200 and len(r.json()["results"]) != 0:
        return parse_open_alex(r.json())
    elif r.status_code == 200 and type == "doi":
        return fetch_crossref(query)
    else:
        return None
    
def fetch_crossref(doi):
    url = f"https://api.crossref.org/works/{doi}"
    try:
        r = requests.get(url, timeout=10)
    except requests.exceptions.ConnectionError:
        return None
    
    if r.status_code == 200:
        return parse_crossref(r.json())
    return None