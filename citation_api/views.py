from django.http import Http404
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle

from common.mixins import ArticleDetailQuerySetMixin
from citation_api.formatters.registry import FORMATTERS

class CitiationExportAPIView(APIView, ArticleDetailQuerySetMixin):
    throttle_classes = [AnonRateThrottle]

    def get(self, request, pk, format_name):
        
        formatter_cls = FORMATTERS.get(format_name)

        if not formatter_cls:
            raise Http404(f"Not supported {format_name} type.",
                          f"Supported formats: {FORMATTERS.keys()}")
        
        artical_object = self.get_queryset_by_pk(pk)

        return formatter_cls().to_response(artical_object)
