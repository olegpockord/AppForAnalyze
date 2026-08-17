from django.http import HttpResponse
from common.mixins import CitiationData

class BaseTemplate:

    content_type = "text/plain"
    inline = True
    extension = "txt"

    def to_response(self, article):
        citiation_data = CitiationData.collect_citiation_data(article)
        content = self.format(citiation_data)
        disposition = "inline" if self.inline else f"attachment; filename=article.{self.extension}"

        response = HttpResponse(content=content, content_type=self.content_type)
        response["Content-Disposition"] = disposition

        return response

    def format(self, data):
        raise NotImplementedError