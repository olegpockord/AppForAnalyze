from django.http import HttpResponse

# Abstract class for other types
class BaseTemplate:

    content_type = "text/plain"
    inline = True
    extension = "txt"

    def to_response(self, article):
        content = self.format(article)
        disposition = "inline" if self.inline else f"attachment; filename=article.{self.extension}"

        response = HttpResponse(content=content, content_type=self.content_type)
        response["Content-Disposition"] = disposition

        return response

    def format(self, article):
        raise NotImplementedError