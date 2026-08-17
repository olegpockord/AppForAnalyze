from common.mixins import AuthorInitialsMixin, CitiationData


class AuthorFormatter(AuthorInitialsMixin):

    def mla(self, main_author, other_authors):
        authors = [self.to_inverted_name(self.get_main_author_initials(main_author))]

        authors.extend(
            self.to_inverted_name(author, reversed=True)
            for author in self.get_other_author_initials(other_authors)
        )

        if len(authors) == 1:
            return f"{authors[0].rstrip('.')}."
        
        elif len(authors) == 2:
            return f"{authors[0]}, and {authors[1].rstrip('.')}."
        
        elif len(authors) == 3:
            return f"{authors[0]}, {authors[1]}, and {authors[2].rstrip('.')}."

        else:
            return f"{authors[0]}, et al."

    def gost(self, main_author, other_authors):
        authors = [self.to_initials_name(self.get_main_author_initials(main_author))]

        authors.extend(
            self.to_initials_name(author)
            for author in self.get_other_author_initials(other_authors)
        )

        if len(authors) > 3:
            return f"{authors[0]} et al."

        return ", ".join(authors)


class CitiationFormatter():
    def __init__(self, article):
        self.author_formatter = AuthorFormatter()
        self.data = CitiationData.collect_citiation_data(article)

    def mla(self):
        authorship = self.author_formatter.mla(self.data.main_author, self.data.other_authors)

        volume = self.data.volume
        issue = self.data.issue

        volume_issue_formatted = None

        if volume and issue:
            volume_issue_formatted = f"{volume}.{issue}"
        elif volume:
            volume_issue_formatted = f"Vol. {volume}."
        elif issue:
            volume_issue_formatted = f"No. {issue}."

        fields = {
            "author": authorship,
            "title": f'"{self.data.title}."',
            "journal": self.data.journal_name,
            "issue&volume": volume_issue_formatted,
            "year": f"({self.data.date.year})",
        }

        citiation =  " ".join(
            value
            for value in fields.values()
            if value
        )

        if self.data.pages:
            citiation = f"{citiation}: {self.data.pages}."

        return citiation

    def gost(self):
        authorship = self.author_formatter.gost(self.data.main_author, self.data.other_authors)

        journal_formatted = f"//{self.data.journal_name}." if self.data.journal_name else None
        volume_formatted = f"– T. {self.data.volume}." if self.data.volume else None
        issue_formatted = f"– №. {self.data.issue}." if self.data.issue else None

        fields = {
            "author": authorship,
            "title": self.data.title,
            "journal": journal_formatted,
            "year": f"– {self.data.date.year}.",
            "volume": volume_formatted,
            "issue": issue_formatted,
            "pages": f"– C. {self.data.pages}."
        }

        return " ".join(
            value
            for value in fields.values()
            if value
        )