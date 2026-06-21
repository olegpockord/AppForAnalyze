from .base import BaseTemplate
from common.mixins import AuthorInitialsMixin

class RisTemplate(BaseTemplate, AuthorInitialsMixin):

    content_type = "application/x-research-information-systems"
    inline = False
    extension = "ris"


    def get_ris_page_range(self, page_range):
        if page_range.find("None") != -1:
            return None, None
        
        dash_index = page_range.find('-')

        start = page_range[:dash_index]
        end = page_range[dash_index + 1:]

        return start, end 
    

    def format(self, article):

        raw_main_author_initials = self.get_main_author_initials(article.articlemainauthor_1[0].main_initials)
        main_author_initials = self.to_inverted_name(raw_main_author_initials).rstrip('.')

        other_authors = article.other_authors
        other_authors_initials = self.get_other_author_initials([author.other_initials for author in other_authors])

        raw_author_list = [main_author_initials]

        for author in other_authors_initials:
            raw_author_list.append(self.to_inverted_name(author).rstrip('.'))

        ready_author_list = "".join(f"\nA1  - {author}" for author in raw_author_list)
            
        start, end = self.get_ris_page_range(article.articalciteinformation_1[0].pages)

        fields = {
            "T1": article.title,
            "JO": article.articalciteinformation_1[0].journal_name,
            "VL": article.articalciteinformation_1[0].volume,
            "IS": article.articalciteinformation_1[0].issue,
            "SP": start,
            "EP": end,
            "DO": article.doi,
            "SN": article.issn,
            "Y1": article.articaldate_1[0].date_of_artical.year,
        }

        body = "".join(
            f"\n{key}  - {value}"
            for key, value in fields.items()
            if value
        )

        return f"TY  - JOUR {ready_author_list}{body}\nER  - "