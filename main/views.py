from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.template.response import TemplateResponse

from main.models import Artical, ArticalCiteData, ArticalCiteInformation, ArticalDate

from main.tasks import dbackup_task
from main.utils import fetch_openalex

from common.mixins import CitiationMixin, GraphMixin

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


class SearchView(TemplateView, CitiationMixin, GraphMixin):
    template_name = "search.html"

    context_object_name = "information"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["name"] = "search"

        query = self.request.GET.get('q').lower()
 
        Artical_set = Artical.objects.filter(doi=str(query)).first()
        
        
        if not Artical_set:
            fetch_openalex(str(query))
            Artical_set = get_object_or_404(Artical, doi=str(query))

        pk = Artical_set.pk

        cite_data_set = ArticalCiteData.objects.select_related("artical").get(artical_id = pk)
        citing_data_set = ArticalCiteInformation.objects.select_related("artical").get(artical_id = pk)
        date_set = ArticalDate.objects.select_related("artical").get(artical_id = pk)

        graph = self.graph_create(cite_data_set)

        cite_data = self.create_cite_data(Artical_set, cite_data_set, citing_data_set, date_set)

        dbackup_task.delay()

        context["artical"] = Artical_set
        context["author_info"] = citing_data_set
        context["date"] = date_set
        context["cite"] = cite_data_set

        context["graph"] = graph
        context["gost"] = cite_data["GOST"]
        context["mla"] = cite_data["MLA"]
        
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return TemplateResponse(request, self.template_name, context)