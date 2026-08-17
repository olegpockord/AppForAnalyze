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

    def format(self, data):
        raw_main_author_initials = self.get_main_author_initials(data.main_author)
        other_authors_initials = self.get_other_author_initials(data.other_authors)
        authors = [raw_main_author_initials, *other_authors_initials]

        ready_authors = [
           {
            "family": f"{author_object.last}",
            "given": " ".join(filter(None, [author_object.first, author_object.middle]))
            }
            for author_object in authors
        ]

        article_date_object =  data.date
        date_parts = {"date-parts": [[article_date_object.year, article_date_object.month, article_date_object.day]]}
            
        fields = {
            "id": f"{raw_main_author_initials.last.lower()}{article_date_object.year}",
            "type": "article-journal",
            "title": data.title,
            "author": ready_authors,
            "issued": date_parts,
            "container-title": data.journal_name,
            "volume": data.volume,
            "issue": data.issue,
            "page": self.get_csl_json_page_range(data.pages),
            "DOI": data.doi,
            "URL": f"https://doi.org/{data.doi}",
            "ISSN": data.issn,
            "ISBN": data.isbn,
            "PMID": data.pmid
        }

        fields = {
            key: value for key, value in fields.items() if value
        }

        return json.dumps(fields, ensure_ascii=False, indent=2)

        