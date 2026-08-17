from .base import BaseTemplate
from common.mixins import AuthorInitialsMixin

class EnwTemplate(BaseTemplate, AuthorInitialsMixin):

    content_type = "text/plain; charset=utf-8"
    inline = False
    extension = "enw"

    def get_enw_page_range(self, page_range):

        if page_range.find("None") != -1:
            return None
        
        return page_range
    
    def format(self, data):

        raw_main_author_initials = self.get_main_author_initials(data.main_author)
        main_author_initials = self.to_inverted_name(raw_main_author_initials)

        other_authors_initials = self.get_other_author_initials(data.other_authors)

        raw_author_list = [main_author_initials]

        for author in other_authors_initials:
            raw_author_list.append(self.to_inverted_name(author))

        ready_author_list = "".join(f"\n%A {author}" for author in raw_author_list)

        fields = {
            "%J": data.journal_name,
            "%V": data.volume,
            "%N": data.issue,
            "%P": self.get_enw_page_range(data.pages),
            "%@": data.issn,
            "%D": data.date.year
        }

        body = "\n".join(
            f"{key} {value}"
            for key, value in fields.items()
            if value
        )

        return f"%0 Journal Article\n%T {data.title}{ready_author_list.replace('.', '')}\n{body}"
