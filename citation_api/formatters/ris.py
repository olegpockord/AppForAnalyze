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
    

    def format(self, data):

        raw_main_author_initials = self.get_main_author_initials(data.main_author)
        main_author_initials = self.to_inverted_name(raw_main_author_initials)
        
        other_authors_initials = self.get_other_author_initials(data.other_authors)

        raw_author_list = [main_author_initials]

        for author in other_authors_initials:
            raw_author_list.append(self.to_inverted_name(author))

        ready_author_list = "".join(f"\nA1  - {author}" for author in raw_author_list)
            
        start, end = self.get_ris_page_range(data.pages)

        fields = {
            "T1": data.title,
            "JO": data.journal_name,
            "VL": data.volume,
            "IS": data.issue,
            "SP": start,
            "EP": end,
            "DO": data.doi,
            "SN": data.issn,
            "Y1": data.date.year,
        }

        body = "".join(
            f"\n{key}  - {value}"
            for key, value in fields.items()
            if value
        )

        return f"TY  - JOUR {ready_author_list.replace('.', '')}{body}\nER  - "