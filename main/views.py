from django.shortcuts import render
from django.views.generic import TemplateView
from django.template.response import TemplateResponse

from main.models import Artical, ArticalCiteData, ArticalDate, ArticalCiteInformation
from main.utils import fetch_crossref, fetch_openalex, set_cache

from common.mixins import GraphMixin 

def test(request):

    query = Artical.objects.filter(doi="10.1038/s41586-020-2649-2".lower())
    print(query)

    if not query:
        fetch_openalex("10.1038/s41586-020-2649-2".lower())


    return render(request, "search.html", context={})


class IndexView(TemplateView):
    template_name = "main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["name"] = "index"
        return context
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return TemplateResponse(request, self.template_name, context)


class SearchView(TemplateView, GraphMixin):
    template_name = "search.html"

    context_object_name = "information"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["name"] = "search"

        query = self.request.GET.get('q').lower()

        Artical_set = Artical.objects.filter(doi=str(query))
        

        if not Artical_set:
            fetch_openalex(str(query))
            Artical_set = Artical.objects.filter(doi=str(query))

        graph = self.graph_create(Artical_set.first())

        Data_sets = Artical_set.prefetch_related(
            "articalcitedata_set",
            "articaldate_set",
            "articalciteinformation_set")
        

        

        #Tecтовые переменные#
        # Author_info_set = ArticalCiteInformation.objects.select_related("artical").get(artical_id = (Artical_set.first().pk))
        
        
        
        # set_cache(f"artical-{query}", Data_sets, 600)

        context["graph"] = graph
        context["articals"] = Data_sets

        
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return TemplateResponse(request, self.template_name, context)