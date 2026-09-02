from datetime import date
from datetime import datetime
from bs4 import BeautifulSoup

from main.models import Artical, ArticalCiteData, ArticalDate, ArticalCiteInformation, ArticleCitePerYear, ArticleMainAuthor, ArticleOtherAuthor, ArticalEmbedding, ArticleSearchVector

from django.db import transaction

def parse_openalex(response):
    articles_to_create = []
    articles_cite_informaion_to_create = []
    articles_date_to_create = []
    articles_cite_data_to_create = []
    articles_citing_per_years_to_create = []
    main_authors_to_create = []
    other_authors_to_create = []
    articles_embedding_to_create = []
    articles_search_vector_to_create = []
    
    exists_doi = set(Artical.objects.filter(doi__in=[
       element.get("ids").get("doi")[16:].lower() for element in response 
       if element.get("ids").get("doi")
    ]).values_list('doi', flat=True))

    exists_mag = set(Artical.objects.filter(mag__in=[
       element.get("ids").get("mag") for element in response 
       if element.get("ids").get("mag")
    ]).values_list('mag', flat=True))

    n = len(response)

    for elem_num in range(n):
        element = response[elem_num]
        ids = element.get("ids")
        doi_raw = ids.get("doi")

        if not doi_raw or not element.get("authorships") or not element.get("title"):
            continue

        title = element.get("title")

        if "<" in title:
            title = BeautifulSoup(title, "html.parser").get_text()
        if len(title) > 298:
            continue

        doi = doi_raw[16:].lower()
        mag = ids.get("mag")

        if doi in exists_doi or mag in exists_mag:
            continue
        
        else:
            exists_doi.add(doi)
            exists_mag.add(mag)

        pmid = ids.get("pmid")[32:] if ids.get("pmid") else None

        source_of_elem = element.get("primary_location").get("source")
        issn_list = source_of_elem.get("issn") if source_of_elem else None
        issn = issn_list[0] if issn_list and len(issn_list) >= 1 else None
        isbn = issn_list[1] if issn_list and len(issn_list) > 1 else None

        article = Artical(
            title = title,
            doi = doi,
            mag = mag,
            pmid = pmid,
            issn = issn,
            isbn = isbn,
            source = "openalex"
        )
        articles_to_create.append(article)

    Artical.objects.bulk_create(articles_to_create)

    articles_by_doi = Artical.objects.in_bulk(
    [a.doi for a in articles_to_create],
    field_name="doi")


    for elem_num in range(n):
        element = response[elem_num]

        doi = element.get("ids").get("doi")

        if not doi:
            continue

        doi = doi[16:].lower()

        article = articles_by_doi.get(doi)
        if not article:
            continue
            
        source = element.get("primary_location").get("source")

        biblio = element.get("biblio")
        journal_name = source.get("display_name") if source else None
        first_page = biblio.get("first_page")
        last_page = biblio.get("last_page")
        volume = biblio.get("volume")
        issue = biblio.get("issue")

        articles_cite_informaion_to_create.append(
            ArticalCiteInformation(
            article = article,
            journal_name = journal_name,
            pages = f"{first_page}-{last_page}",
            volume = volume,
            issue = issue
        ))

        abstract = element.get("abstract_inverted_index")

        if abstract:
            articles_embedding_to_create.append(
                ArticalEmbedding(
                article = article,
                abstract_text = f"{article.title}\n" + " ".join(abstract)
            ))

        articles_search_vector_to_create.append(ArticleSearchVector(article=article))            

        date_of_artical = date.fromisoformat(element.get("publication_date"))

        articles_date_to_create.append(
            ArticalDate(
            article = article,
            date_of_artical = date_of_artical,
        ))

        cited_by_count = int(element.get("cited_by_count"))
        reference_in_work = int(element.get("referenced_works_count"))

        articles_cite_data_to_create.append(ArticalCiteData(
            article = article,
            reference_count = cited_by_count,
            reference_in_work = reference_in_work
        ))

        citing_by_years = element.get("counts_by_year")

        for citing in citing_by_years:
            year = int(citing['year'])
            citiation = int(citing['cited_by_count'])

            articles_citing_per_years_to_create.append(ArticleCitePerYear(
                article = article,
                year = year,
                citiation = citiation,
            ))

        authorships = element.get("authorships")

        for i, some_author in enumerate(authorships):
            author = some_author.get("author").get("display_name")

            if author.find('.', 0, 3) == 1 and author[2] != ' ': # Helps with "A.A. Last" problem -> A. A. Last
                author = f"{author[:2]} {author[2:]}"

            if i == 0:
                main_authors_to_create.append(
                    ArticleMainAuthor(
                    article = article,
                    main_initials = author,
                ))
                
            else:
                other_authors_to_create.append(ArticleOtherAuthor(
                    article = article,
                    other_initials = author,
                ))

            if i >= 3: break

    with transaction.atomic():
        ArticalCiteInformation.objects.bulk_create(articles_cite_informaion_to_create)
        ArticalDate.objects.bulk_create(articles_date_to_create)
        ArticalCiteData.objects.bulk_create(articles_cite_data_to_create)
        ArticleCitePerYear.objects.bulk_create(articles_citing_per_years_to_create)
        ArticleMainAuthor.objects.bulk_create(main_authors_to_create)
        ArticleOtherAuthor.objects.bulk_create(other_authors_to_create)
        ArticalEmbedding.objects.bulk_create(articles_embedding_to_create)
        ArticleSearchVector.objects.bulk_create(articles_search_vector_to_create)
        

    return list(articles_by_doi.keys()) or []


def parse_crossref(response):
    other_authors_to_create = []   

    authorship = response.get("author")
    doi = response.get("DOI")

    if not authorship or not doi:
        return None
    
    title = response.get("title")[0]
    doi = doi.lower()
    issn_list = response.get("ISSN")
    issn = issn_list[0] if issn_list else None
    isbn = issn_list[1] if issn_list and len(issn_list) > 1 else None

    article = Artical(
            title = title,
            doi = doi,
            issn = issn,
            isbn = isbn,
            source = "crossref"
        )

    journal_name = response.get("container-title")[0] if response.get("container-title") else None
    pages = response.get("page")
    volume = response.get("volume")
    issue = response.get("issue")

    article_cite_information = ArticalCiteInformation(
            article = article,
            journal_name = journal_name,
            pages = pages,
            volume = volume,
            issue = issue
        )

    timestamp = int(response['created']['timestamp']) // 1000
    date_of_artical = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

    artical_date = ArticalDate(
            article = article,
            date_of_artical = date_of_artical,
        )
    
    cited_by_count = int(response.get("is-referenced-by-count"))
    reference_in_work = int(response.get("reference-count"))

    artical_cite_data = ArticalCiteData(
            article = article,
            reference_count = cited_by_count,
            reference_in_work = reference_in_work
        )

    for i, some_author in enumerate(authorship):
            first_name = some_author.get("given")
            last_name = some_author.get("family")
            author = f"{first_name} {last_name}"

            if i == 0:
                first_author = author

                article_main_author = ArticleMainAuthor(
                    article = article,
                    main_initials = first_author,
                )

            else:
                other_author = author

                article_other_author = ArticleOtherAuthor(
                    article = article,
                    other_initials = other_author,
                )

                other_authors_to_create.append(article_other_author)
            if i>=3: break

    with transaction.atomic():
        article.save()
        article_cite_information.save()
        artical_date.save()
        artical_cite_data.save()
        article_main_author.save()
        ArticleOtherAuthor.objects.bulk_create(other_authors_to_create)

    return list(doi)

class OpenalexArticleParser:

    def parse_and_create(self, json_data):
        return parse_openalex(json_data)
        
    def parse_citation(self, data):
        data = data[0]
        return {
            "cited_by_count": int(data.get("cited_by_count")),
            "reference_in_work": int(data.get("referenced_works_count"))
        }

    def parse_citation_by_year(self, data):
        data = data[0]
        return {"citing_by_years": data.get("counts_by_year")}

class CrossrefArticleParser:

    def parse_and_create(self, json_data):
        return parse_crossref(json_data)

    def parse_citation(self, data):
        return {
            "cited_by_count": int(data.get("is-referenced-by-count")),
            "reference_in_work": int(data.get("reference-count"))
        }