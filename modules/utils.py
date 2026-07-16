import re
import uuid

from main.models import Artical
from modules.services.external_requests import fetch_openalex
from modules.services.custom_exceptions import SearchSearchExpired

from django.http import Http404
from django.core.cache import cache
from django.utils.translation import gettext as _
from django.contrib import messages


def detect_pattern_type(query):
    doi_pattern = r'^10\.'
    mag_pattern = r'^mag\d'
    pmid_pattern = r'^pmid\d'

    detected = "search="
    if re.match(doi_pattern, query):
        detected = "filter=doi:"

    elif re.match(mag_pattern, query):
        detected = "filter=mag:"

    elif re.match(pmid_pattern, query):
        detected = "filter=pmid:"
    return detected


def search_type(query):

    pattern = detect_pattern_type(query)
    addition = ''

    if pattern == "search=":
        return None
    
    query = query.lower().strip()

    if pattern != "filter=doi:":
        first_num_include = re.compile(r'\d')
        first_include_index = re.search(first_num_include, query)
        query = query[first_include_index.start():]

    pattern_kwargs = {f"{pattern[7:-1]}": query}
    article = Artical.objects.filter(**pattern_kwargs).first()

    if article:
        return article.pk
        
    fetch_openalex(pattern, query, addition)

    try:
        res = Artical.objects.filter(**pattern_kwargs).first().pk
    except AttributeError:
        raise Http404

    return res

def get_openalex_dois(self, query, update_time=180):

    sid = self.request.GET.get("sid")

    if sid:
        dois = cache.get(f"openalex:{sid}")

        if dois is None:
            messages.warning(self.request, _("Время сессии истекло, вы возвращены на главную")) # Session time expired, you returned on main page
            raise SearchSearchExpired

        cache.touch(f"openalex:{sid}", update_time)
        return dois

    created_dois = fetch_openalex("search=", query.strip().replace(' ', '+'), optional="&per-page=50")

    sid = uuid.uuid4().hex

    cache.set(f"openalex:{sid}", created_dois, 180)

    self.sid = sid

    return created_dois

# def parse_openalex(response):
#     new_parse_open_alex(response)
#     raw_json = response["results"]
#     for num, x in enumerate(raw_json):
#         element = raw_json[num]

#         if element.get("ids").get("doi") and element.get("authorships"):
#             title = element.get("title")
#             title = BeautifulSoup(title, "html.parser").get_text()
#             if len(title) > 298: continue
#             ids = element.get("ids")
#             doi = ids.get("doi")[16:].lower()
#             mag = ids.get("mag")
#             pmid = ids.get("pmid")[32:] if ids.get("pmid") else None

#             if Artical.objects.filter(doi=doi).exists(): # Временная заглушка, мб добавить дата обновления < 3 или что-то еще
#                 continue

#             source_of_elem = element.get("primary_location").get("source")
#             issn_list = source_of_elem.get("issn") if source_of_elem else None
#             issn = issn_list[0] if issn_list and len(issn_list) >= 1 else None
#             isbn = issn_list[1] if issn_list and len(issn_list) > 1 else None

#             article = Artical.objects.create(
#                 title = title,
#                 doi = doi,
#                 mag = mag,
#                 pmid = pmid,
#                 issn = issn,
#                 isbn = isbn,
#                 source = "openalex",
#             )

#             biblio = element.get("biblio")
#             journal_name = source_of_elem.get("display_name") if source_of_elem else None
#             first_page = biblio.get("first_page")
#             last_page = biblio.get("last_page")
#             volume = biblio.get("volume")
#             issue = biblio.get("issue")

#             article_cite_information = ArticalCiteInformation.objects.create(
#                 article = article,
#                 journal_name = journal_name,
#                 pages = f"{first_page}-{last_page}",
#                 volume = volume,
#                 issue = issue,
#             )

#             date_of_artical = datetime.strptime(element.get("publication_date"), "%Y-%m-%d").date()

#             artical_date = ArticalDate.objects.create(
#                 article = article,
#                 date_of_artical = date_of_artical,
#             )

#             cited_by_count = int(element.get("cited_by_count"))
#             reference_in_work = int(element.get("referenced_works_count"))

#             artical_cite_data = ArticalCiteData.objects.create(
#                 article = article,
#                 reference_count = cited_by_count,
#                 reference_in_work = reference_in_work,
#             )

#             citing_by_years = element.get("counts_by_year")

#             for citing in citing_by_years:
#                 year = int(citing['year'])
#                 citiation = int(citing['cited_by_count'])

#                 article_cite_per_year = ArticleCitePerYear.objects.create(
#                     article = article,
#                     year = year,
#                     citiation = citiation,
#                 )

#             authorships = element.get("authorships")

#             for i, some_author in enumerate(authorships):
#                 author = some_author.get("author").get("display_name")

#                 if author.find('.', 0, 3) == 1 and author[2] != ' ': # Helps with "A.A. Last" problem -> A. A. Last
#                     author = f"{author[:2]} {author[2:]}"

#                 if i == 0:
#                     first_author = author  # В этих условиях делаем их добавление

#                     article_main_author = ArticleMainAuthor.objects.create(
#                         article = article,
#                         main_initials = first_author,
#                     )
                
#                 else:
#                     other_author = author

#                     article_other_author = ArticleOtherAuthor.objects.create(
#                         article = article,
#                         other_initials = other_author,
#                     )

#                 if i >= 3: break

# def parse_crossref(response):
#     element = response["message"]

#     title = element.get("title")[0]
#     doi = element.get("DOI").lower()
#     issn_list = element.get("ISSN")
#     issn = issn_list[0] if issn_list and len(issn_list) >= 1 else None
#     isbn = issn_list[1] if issn_list and len(issn_list) > 1 else None

#     journal_name = element.get("container-title")[0] if element.get("container-title") else None
#     pages = element.get("page")
#     volume = element.get("volume")
#     issue = element.get("issue")

#     timestamp = int(element['created']['timestamp']) // 1000
#     date_of_artical = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

#     reference_count = int(element.get("is-referenced-by-count"))
#     reference_in_work = int(element.get("reference-count"))

#     authorship = element.get("author")

#     for i, some_author in enumerate(authorship):
#         first_name = some_author.get("given")
#         last_name = some_author.get("family")
#         author = f"{first_name} {last_name}"

#         if i == 0:
#             first_author = author
#         else:
#             other_author = author
#         if i>=3: break


# def parse_openalex(response):

#     data = response.json()["results"][0]

#     try:
#         first_page = data["biblio"]["first_page"]
#         last_page = data["biblio"]["last_page"]

#         safety_data = get_safety_data_openalex(data)

#         date_of_artical = datetime.strptime(data["publication_date"], "%Y-%m-%d").date()
        
#         with transaction.atomic():
            
            # artical = Artical.objects.create(
            #     title = data["title"],
            #     doi = (data["doi"][16::]).lower(),
            #     mag = safety_data["mag"],
            #     pubmed = safety_data["pubmed"][32::] if safety_data["pubmed"] else None,
            #     issn = safety_data["issn"],
            #     isbn = safety_data["isbn"],
            # )

            # artical_cite_data = ArticalCiteData.objects.create(
            #     artical = artical,
            #     raw = data,
            #     reference_count = data["referenced_works_count"],
            #     reference_in_work = int(data["cited_by_count"]),
            # )

            # artical_date = ArticalDate.objects.create(
            #     artical = artical,
            #     date_of_artical = date_of_artical,
            # )

            # artical_cite_information = ArticalCiteInformation.objects.create(
            #     artical = artical,
            #     journal_name = data["primary_location"]["source"]["display_name"],
            #     pages = f"{first_page}-{last_page}",
            #     volume = safety_data["volume"],
            #     author = data["authorships"][0]["raw_author_name"], # Придумать нормализацию в дальнейшем
            #     issue = data["biblio"]["issue"],
            # )
#     except Exception:
#         raise Http404("При получении данных о статье возникла ошибка")
        

# def parse_crossref(response):
#     data = response.json()["message"]

#     try:
#         timestamp = int(data['created']['timestamp']) // 1000
#         date_of_artical = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

#         first_name = data["author"][0]["given"]
#         last_name = data["author"][0]["family"]



#         with transaction.atomic():
#             artical = Artical.objects.create(
#                 title = data["title"][0],
#                 doi = (data["DOI"]).lower(),
#                 issn = data.get("ISSN")[0] if data.get("ISSN") else None,
#                 isbn = data.get("ISSN")[1] if data.get("ISSN") else None,
#             )

#             artical_cite_data = ArticalCiteData.objects.create(
#                 artical = artical,
#                 raw = data,
#                 reference_count = int(data["reference-count"]),
#                 reference_by_count = int(data["is-referenced-by-count"]),
#                 source = "crossref",
#             )

#             artical_date = ArticalDate.objects.create(
#                 artical = artical,
#                 date_of_artical = date_of_artical,
#             )

#             artical_cite_information = ArticalCiteInformation.objects.create(
#                 artical = artical,
#                 journal_name = data["container-title"][0],
#                 pages = data["page"],
#                 volume = data.get("volume"),
#                 author = f"{last_name} {first_name}",
#                 issue = data["issue"],
#             )
#     except Exception:
#         raise Http404("При получении данных о статье возникла ошибка")
        

# def get_safety_data_openalex(response):
#     ids = response.get("ids")

#     mag = ids.get("mag")
#     pmid = ids.get("pmid")

#     issn_list = (response.get("primary_location", {}) .get("source", {}) .get("issn")) or []

#     issn = issn_list[0] if len(issn_list) > 1 else None
#     isbn = issn_list[1] if len(issn_list) > 1 else None

#     volume = response.get("biblio").get("volume")

#     return {
#         "mag": mag,
#         "pubmed": pmid,
#         "issn": issn,
#         "isbn": isbn,
#         "volume": volume,
#     }