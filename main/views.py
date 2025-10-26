from django.shortcuts import render
from django.views.generic import TemplateView
from django.template.response import TemplateResponse

from main.models import Artical
from main.utils import fetch_openalex



from common.mixins import GraphMixin, CitiationMixin, CacheMixin 

def test(request):

    query = Artical.objects.filter(doi="10.1038/s41586-020-2649-2".lower())
    print(query)

    if not query:
        fetch_openalex("10.1038/s41586-020-2649-2".lower())
    
    # 10.1109/MCSE.2011.37
    # 10.1371/journal.ppat.1006698
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


class SearchView(TemplateView, GraphMixin, CitiationMixin, CacheMixin):
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

        

        current_artical = Artical_set.first()

        graph = self.graph_create(current_artical)

        cite_data = self.create_cite_data(current_artical)

        # Протестить .annotate метод для начального поля

        Data_sets = Artical_set.prefetch_related(
            "articalcitedata_set",
            "articaldate_set",
            "articalciteinformation_set")
        

        context["graph"] = graph
        context["gost"] = cite_data["GOST"]
        context["mla"] = cite_data["MLA"]
        context["articals"] = self.set_get_cache(f"prefetchcache-{query}", Data_sets, 60 * 1)

        
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return TemplateResponse(request, self.template_name, context)