from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from modules.services.nameparser_constants import get_extend_constants
from main.models import Artical, ArticleCitePerYear, ArticleOtherAuthor

from nameparser import HumanName
from dataclasses import dataclass
from datetime import datetime

class AuthorInitialsMixin:

    C = get_extend_constants()

    def get_main_author_initials(self, main_author):

        author_initials = HumanName(main_author, constants=self.C)

        return author_initials
    
    def get_other_author_initials(self, other_authors):

        if not other_authors:
            return []

        other_authors_initials = [HumanName(author, constants=self.C) for author in other_authors]

        return other_authors_initials

    def normalize_author_part(self, author_part):
        if not author_part:
            return None

        value = author_part.strip()

        if len(value.rstrip('.')) == 1:
            return f"{value.rstrip('.')}."

        return value
    
    def to_inverted_name(self, human_initials, reversed = False):

        last_name = self.normalize_author_part(human_initials.last)
        first_name = self.normalize_author_part(human_initials.first)
        middle_name = self.normalize_author_part(human_initials.middle)

        if reversed:
            if middle_name:
                return f"{first_name} {middle_name} {last_name}"
            
            else:
                return f"{first_name} {last_name}"

        full_inverted_name = f"{last_name}, {first_name}"

        if middle_name:
            full_inverted_name += f" {middle_name}"

        return full_inverted_name

    def to_initials_name(self, human_initials):
        
        last_name = human_initials.last
        first_name = human_initials.first
        middle_name = human_initials.middle

        full_initials_name = f"{last_name} {first_name[0]}."

        if middle_name:
            full_initials_name += f" {middle_name[0]}."

        return full_initials_name


@dataclass
class CitiationData:
    title: str
    doi: str
    main_author: str
    date: datetime.date

    pmid: str | None=None
    issn: str | None=None
    isbn: str | None=None

    journal_name: str | None=None
    pages: str | None=None
    volume: str | None=None
    issue: str | None=None

    other_authors: list[str] | None=None

    @classmethod
    def collect_citiation_data(cls, article):
        cite_info = article.articalciteinformation_1[0]

        other_authors = article.other_authors
        other_authors_initials = [author.other_initials for author in other_authors]

        return cls(
            title=article.title,
            doi = article.doi,
            main_author = article.articlemainauthor_1[0].main_initials,
            date = article.articaldate_1[0].date_of_artical,
            pmid = article.pmid,
            issn = article.issn,
            isbn = article.isbn,
            journal_name = cite_info.journal_name,
            pages = cite_info.pages,
            volume = cite_info.volume,
            issue = cite_info.issue,
            other_authors = other_authors_initials
        )


class ArticleDetailQuerySetMixin:
    
    def get_queryset(self):

        query_set =  Artical.objects.prefetch_related(
            Prefetch('articalciteinformation_set', to_attr="articalciteinformation_1"),
            Prefetch('articaldate_set', to_attr="articaldate_1"),
            Prefetch('articalcitedata_set', to_attr="articalcitedata_1"),
            Prefetch('articlemainauthor_set', to_attr="articlemainauthor_1"),
            Prefetch('articleciteperyear_set', 
                queryset=ArticleCitePerYear.objects.all(),
                to_attr='citing_per_year'),
            Prefetch('articleotherauthor_set',
                queryset=ArticleOtherAuthor.objects.all(),
                to_attr="other_authors"),
            )

        return query_set
    
    def get_queryset_by_pk(self, pk):
        
        query_set = self.get_queryset()

        return get_object_or_404(query_set, id=pk)


# Old citiations for GOST and MLA
# class CitiationMixin(AuthorInitialsMixin):


#     def author_parser(self, main_author, other_authors):

#         main_author_initials = self.get_main_author_initials(main_author)

#         main_author_gost_name = self.to_initials_name(main_author_initials)
#         main_author_mla_name = self.to_inverted_name(main_author_initials)

#         other_authors_initials = self.get_other_author_initials(other_authors)
#         other_authors_len = len(other_authors_initials)

#         prepared_main_author_mla_name = main_author_mla_name[:-1] if main_author_mla_name.endswith("..") else main_author_mla_name.rstrip('.') # ".." if middle name present # Problem with 1 word

#         if other_authors_len == 0:
#             return {
#                 "mla": f"{prepared_main_author_mla_name.rstrip('.')}.",
#                 "gost": main_author_gost_name,
#             }
        
#         if other_authors_len > 2:
#             return {
#                 "mla": f"{prepared_main_author_mla_name}, et al.",
#                 "gost": f"{main_author_gost_name} et al.",
#             }

#         other_mla_citing = []
#         main_author_mla_name = ""

#         for author in other_authors_initials:
#             other_author_gost_name = self.to_initials_name(author)
#             main_author_gost_name = f"{main_author_gost_name}, {other_author_gost_name}"
#             other_author_mla_name = self.to_inverted_name(author, reversed=True)
#             other_mla_citing.insert(0, other_author_mla_name)

#         main_author_mla_name = f"{prepared_main_author_mla_name}, and {other_mla_citing[0]}."

#         if len(other_mla_citing) > 1:
#             main_author_mla_name = f"{prepared_main_author_mla_name}, {other_mla_citing[1]}, and {other_mla_citing[0]}."
        
#         return {
#             "mla": main_author_mla_name,
#             "gost": main_author_gost_name,
#         }

            
#     def create_cite_data(self, article_qs):
#         title = article_qs.title

#         date = article_qs.articaldate_1[0].date_of_artical

#         article_data_for_cite = article_qs.articalciteinformation_1[0]
#         journal = article_data_for_cite.journal_name
#         pages = article_data_for_cite.pages
#         volume = article_data_for_cite.volume
#         issue = article_data_for_cite.issue

#         main_author = article_qs.articlemainauthor_1[0].main_initials

#         other_authors = article_qs.other_authors
#         other_authors = [i.other_initials for i in other_authors]

#         authors = self.author_parser(main_author, other_authors)

#         author_gost = authors["gost"]
#         author_mla = authors["mla"]

#         cite_data_set = {}

#         check_volume_gost = f"— T.{volume}."

#         gost_cite = f"{author_gost} {title} //{journal if journal else 'No information found about journal'}. — {date.year}. {check_volume_gost if volume else ''} {'—№. '+issue if issue else ''} —C. {pages}"
#         mla_cite = f"{author_mla} {chr(34)+title+chr(34)} {journal if journal else 'No information found about journal'} {volume if volume else ''}{'.' + issue if issue else ''} {chr(40)+str(date.year)+chr(41)}: {pages}"

#         cite_data_set = {
#             "GOST": gost_cite,
#             "MLA": mla_cite,
#         }

#         return cite_data_set