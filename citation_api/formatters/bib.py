from .base import BaseTemplate
from common.mixins import AuthorInitialsMixin

class BibTexTemplate(BaseTemplate, AuthorInitialsMixin):

    content_type = "text/plain; charset=utf-8"
    inline = True
    extension = "bib"

    def get_bibtex_page_range(self, page_range):

        if page_range.find("None") != -1:
            return None

        dash_index = page_range.find('-')
        page_range_for_bib = f"{page_range[:dash_index]}-{page_range[dash_index:]}"

        return page_range_for_bib

    def format(self, data):

        raw_main_author_initials = self.get_main_author_initials(data.main_author)
        main_author_initials = self.to_inverted_name(raw_main_author_initials)

        other_authors_initials = self.get_other_author_initials(data.other_authors)

        raw_author_list = [main_author_initials]

        for author in other_authors_initials:
            raw_author_list.append(self.to_inverted_name(author))

        ready_list = " and ".join(raw_author_list).replace('.', '')

        fields = {
            "title": data.title,
            "author": ready_list,
            "journal": data.journal_name,
            "volume": data.volume,
            "number": data.issue,
            "pages": self.get_bibtex_page_range(data.pages),
            "year": data.date.year
        }

        body = ",\n".join(
            f"  {key}={{{value}}}"
            for key, value in fields.items()
            if value
        )

        head = f"{raw_main_author_initials.last.lower()}{fields['year']},\n" # AuthorLastNameYear
    
        return f"@article{{{head}{body}\n}}"
