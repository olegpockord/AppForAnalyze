from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.template.response import TemplateResponse

from main.models import Artical, ArticalCiteData, ArticalCiteInformation, ArticalDate

from modules.utils import fetch_openalex

from common.mixins import CitiationMixin, GraphMixin

import re


class SearchView(TemplateView, CitiationMixin, GraphMixin):
    template_name = "search.html"

    context_object_name = "information"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["name"] = "search"

        query = self.request.GET.get('q').strip()

        doi_pattern = r'^10\.'
        mag_pattern = r'\bmag*'
        pmid_pattern = r'\bpmid*'

        addition = ''

        if re.match(doi_pattern, query):
            type = "filter=doi:"
        elif re.match(mag_pattern, query):
            type = "filter=mag:"
        elif re.match(pmid_pattern, query):
            type = "filter=pmid:"
        else:
            type = "search="
            query = query.replace(' ', '+')
            addition = "&per-page=50"
 

        fetch_openalex(type, query, addition)

        # query = self.request.GET.get('q').lower()

        # Artical_set = Artical.objects.filter(doi=str(query)).first()
        
        
        # if not Artical_set:
        #     fetch_openalex(str(query))
        #     Artical_set = get_object_or_404(Artical, doi=str(query))

        # pk = Artical_set.pk

        # cite_data_set = ArticalCiteData.objects.select_related("artical").get(artical_id = pk)
        # citing_data_set = ArticalCiteInformation.objects.select_related("artical").get(artical_id = pk)
        # date_set = ArticalDate.objects.select_related("artical").get(artical_id = pk)

        # graph = self.graph_create(cite_data_set)

        # cite_data = self.create_cite_data(Artical_set, cite_data_set, citing_data_set, date_set)


        # context["artical"] = Artical_set
        # context["author_info"] = citing_data_set
        # context["date"] = date_set
        # context["cite"] = cite_data_set

        # context["graph"] = graph
        # context["gost"] = cite_data["GOST"]
        # context["mla"] = cite_data["MLA"]

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return TemplateResponse(request, self.template_name, context)
