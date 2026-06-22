from .base import BaseTemplate
from common.mixins import AuthorInitialsMixin

class EnwTemplate(BaseTemplate, AuthorInitialsMixin):

    content_type = "text/plain"
    inline = False
    extension = "enw"

    def get_enw_page_range(self, page_range):

        if page_range.find("None") != -1:
            return None
        
        return page_range
    
    def format(self, article):

        raw_main_author_initials = self.get_main_author_initials(article.articlemainauthor_1[0].main_initials)
        main_author_initials = self.to_inverted_name(raw_main_author_initials).rstrip('.')

        other_authors = article.other_authors
        other_authors_initials = self.get_other_author_initials([author.other_initials for author in other_authors])

        raw_author_list = [main_author_initials]

        for author in other_authors_initials:
            raw_author_list.append(self.to_inverted_name(author).rstrip('.'))

        ready_author_list = "".join(f"\n%A {author}" for author in raw_author_list)

        fields = {
            "%J": article.articalciteinformation_1[0].journal_name,
            "%V": article.articalciteinformation_1[0].volume,
            "%N": article.articalciteinformation_1[0].issue,
            "%P": self.get_enw_page_range(article.articalciteinformation_1[0].pages),
            "%@": article.issn,
            "%D": article.articaldate_1[0].date_of_artical.year
        }

        body = "\n".join(
            f"{key} {value}"
            for key, value in fields.items()
            if value
        )

        return f"%0 Journal Article\n%T {article.title}{ready_author_list}\n{body}"
