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


    def format(self, article):

        raw_main_author_initials = self.get_main_author_initials(article.articlemainauthor_1[0].main_initials)
        main_author_initials = self.to_inverted_name(raw_main_author_initials).rstrip('.')

        other_authors = article.other_authors
        other_authors_initials = self.get_other_author_initials([author.other_initials for author in other_authors])

        raw_author_list = [main_author_initials]

        for author in other_authors_initials:
            raw_author_list.append(self.to_inverted_name(author).rstrip('.'))

        ready_list = " and ".join(raw_author_list).rstrip()

        fields = {
            "title": article.title,
            "author": ready_list,
            "journal": article.articalciteinformation_1[0].journal_name,
            "volume": article.articalciteinformation_1[0].volume,
            "number": article.articalciteinformation_1[0].issue,
            "pages": self.get_bibtex_page_range(article.articalciteinformation_1[0].pages),
            "year": article.articaldate_1[0].date_of_artical.year
        }

        body = ",\n".join(
            f"  {key}={{{value}}}"
            for key, value in fields.items()
            if value
        )

        head = f"{raw_main_author_initials.last.lower()}{fields['year']},\n" # AuthorLastNameYear
    
        return f"@article{{{head}{body}\n}}"
