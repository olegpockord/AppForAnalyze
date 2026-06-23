from .base import BaseTemplate
from common.mixins import AuthorInitialsMixin
import json

class CSLJsonTemplate(BaseTemplate, AuthorInitialsMixin):
    content_type  = "application/json"
    inline = True
    extension = "json"

    def get_csl_json_page_range(self, page_range):

        if page_range.find("None") != -1:
            return None
        
        return page_range

    def format(self, article):
        raw_main_author_initials = self.get_main_author_initials(article.articlemainauthor_1[0].main_initials)

        other_authors = article.other_authors
        other_authors_initials = self.get_other_author_initials([author.other_initials for author in other_authors])
        authors = [raw_main_author_initials, *other_authors_initials]

        ready_authors = [
           {
            "family": f"{author_object.last}",
            "given": " ".join(filter(None, [author_object.first, author_object.middle]))
            }
            for author_object in authors
        ]

        article_date_object =  article.articaldate_1[0].date_of_artical
        date_parts = {"date-parts": [[article_date_object.year, article_date_object.month, article_date_object.day]]}
            
        fields = {
            "id": f"{raw_main_author_initials.last.lower()}{article.articaldate_1[0].date_of_artical.year}",
            "type": "article-journal",
            "title": article.title,
            "author": ready_authors,
            "issued": date_parts,
            "container-title": article.articalciteinformation_1[0].journal_name,
            "volume": article.articalciteinformation_1[0].volume,
            "issue": article.articalciteinformation_1[0].issue,
            "page": self.get_csl_json_page_range(article.articalciteinformation_1[0].pages),
            "DOI": article.doi,
            "URL": f"https://doi.org/{article.doi}",
            "ISSN": article.issn,
            "ISBN": article.isbn,
            "PMID": article.pmid
        }

        fields = {
            key: value for key, value in fields.items() if value
        }

        return json.dumps(fields, ensure_ascii=False, indent=2)

        