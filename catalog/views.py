from django.shortcuts import redirect
from django.views.generic import ListView, DetailView
from django.urls import reverse
from django.db.models import OuterRef, Subquery, Q
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from main.models import Artical, ArticalCiteData, ArticalDate, ArticleMainAuthor
from modules.utils import search_type, get_openalex_dois
from catalog.mixins import GraphMixin, SearchMixin
from common.mixins import ArticleDetailQuerySetMixin, CitiationMixin
from modules.services.recommendations import get_article_recommendations
from modules.services.custom_exceptions import SearchSessionExpired
from citation_api.formatters.registry import FORMATTERS

class CatalogView(ListView, SearchMixin):
    model = Artical
    template_name = "catalog.html"
    context_object_name = "articles"
    paginate_by = 15
    page_kwarg = 'p'

    SORT_MAPPING = {
        "default": "-pk",
        "latest": "-publish_date",
        "mostcited": "-cite_count",
        "uplouddate": "-update_date",
    }

    def display_fields(self, qs):
        return qs.annotate(
            main_author_initials=Subquery(
            ArticleMainAuthor.objects
            .filter(article=OuterRef('pk'))
            .values('main_initials')[:1]
            ),
            publish_date=Subquery(
            ArticalDate.objects
            .filter(article=OuterRef('pk'))
            .values('date_of_artical')[:1]
            ),
            update_date = Subquery(
            ArticalDate.objects
            .filter(article=OuterRef('pk'))
            .values('date_of_last_update')[:1]
            ),
            cite_count=Subquery(
            ArticalCiteData.objects
            .filter(article=OuterRef('pk'))
            .values('reference_count')[:1]
            ),
            )
        # Method with F slower with paginator, but significantly faster with query itself, subquery win in just 2-3ms
        # return qs.annotate(
        #     main_author_initials=F("articlemainauthor__main_initials"),
        #     publish_date=F("articaldate__date_of_artical"),
        #     update_date=F("articaldate__date_of_last_update"),
        #     cite_count=F("articalcitedata__reference_count")
        # )

    def get_queryset(self):
        base_query_set = Artical.objects.all()

        query = self.request.GET.get('q')
        param_for_api = self.request.GET.get("scope")
        sort_param = self.request.GET.get("sort")
        param = self.SORT_MAPPING.get(sort_param, '-pk')

        if not query:
            return self.display_fields(base_query_set).order_by(param, '-pk')

        search_ids = self.full_text_search(query)
        created_articles_dois = []
        
        if param_for_api or self.request.GET.get("sid"):
            
            created_articles_dois = get_openalex_dois(self, query)

        query_set = base_query_set.filter(Q(pk__in=search_ids or []) | Q(doi__in=created_articles_dois or []))

        return self.display_fields(query_set).order_by(param, '-pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["name"] = "catalog" 
        context["sid"] = getattr(self, "sid", None)

        return context
    
    def get(self, request, *args, **kwargs):

        query = self.request.GET.get('q')

        if query:
            qs = search_type(query)

            if qs:
                return redirect(
                    reverse("catalog:work_detail", kwargs={'pk': qs})
                )
            
        try:
            return super().get(request, *args, **kwargs)
        except SearchSessionExpired:
            return redirect(reverse("main:index"))


@method_decorator(cache_page(60 * 15), name="dispatch")    
class WorkDetailView(ArticleDetailQuerySetMixin, DetailView, GraphMixin, CitiationMixin):
    model = Artical
    template_name = "work_detail.html"
    slug_field = 'pk'
    slug_url_kwarg = 'pk'
    context_object_name = "article"
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = context["article"]

        context["artical_cite_information"] = article.articalciteinformation_1[0]
        context["artical_date"] = article.articaldate_1[0]
        context["article_main_author"] = article.articlemainauthor_1[0]
        context["artical_cite_data"] = article.articalcitedata_1[0]

        context["name"] = article.title

        graph = self.graph_create(article)

        cite_types = self.create_cite_data(article)

        context["graph"] = graph
        context["gost"] = cite_types["GOST"]
        context["mla"] = cite_types["MLA"]
        context["citation_formats"] = list(FORMATTERS.keys())

        context["recommendations"] = get_article_recommendations(self.object.pk)

        return context
