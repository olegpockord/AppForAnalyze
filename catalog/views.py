from django.shortcuts import redirect
from django.views.generic import ListView, DetailView
from django.urls import reverse
from django.db.models import OuterRef, Subquery, Prefetch, Q
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from main.models import Artical, ArticalCiteData, ArticalDate, ArticleCitePerYear, ArticleMainAuthor, ArticleOtherAuthor
from modules.utils import fetch_openalex, search_type
from common.mixins import CitiationMixin, GraphMixin, SearchMixin
from modules.services.recommendations import get_article_recommendations


class CatalogView(ListView, SearchMixin):
    model = Artical
    template_name = "catalog.html"
    context_object_name = "articles"
    paginate_by = 15
    page_kwarg = 'p'

    SORT_MAPPING = {
        "default": "pk",
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

    def search_fields(self, qs):
        return qs.annotate(
            main_author_initials=Subquery(
            ArticleMainAuthor.objects
            .filter(article=OuterRef('pk'))
            .values('main_initials')[:1]
            )
        )

    def get_queryset(self):
        base_query_set =  Artical.objects.all()

        query = self.request.GET.get('q')
        param_for_api = self.request.GET.get("scope")
        sort_param = self.request.GET.get("sort")
        param = self.SORT_MAPPING.get(sort_param, 'pk')

        # query_set = query_set.annotate(
        #     main_author_initials=Subquery(
        #     ArticleMainAuthor.objects
        #     .filter(article=OuterRef('pk'))
        #     .values('main_initials')[:1]
        #     ),
        #     publish_date=Subquery(
        #     ArticalDate.objects
        #     .filter(article=OuterRef('pk'))
        #     .values('date_of_artical')[:1]
        #     ),
        #     update_date = Subquery(
        #     ArticalDate.objects
        #     .filter(article=OuterRef('pk'))
        #     .values('date_of_last_update')[:1]
        #     ),
        #     cite_count=Subquery(
        #     ArticalCiteData.objects
        #     .filter(article=OuterRef('pk'))
        #     .values('reference_count')[:1]
        #     ),
        #     )
        
        if not query:
            return self.display_fields(base_query_set).order_by(param, 'pk')
        
        search_fields_query_set = self.search_fields(base_query_set) 
        query_set = self.q_search(query, search_fields_query_set)

        if param_for_api:
            created_articles = fetch_openalex("search=", query.strip().replace(' ', '+'), optional="&per-page=50")

            ids_in_search = list(query_set.values_list("id", flat=True))

            query_set = base_query_set.filter(Q(pk__in=ids_in_search) | Q(doi__in=created_articles))

        return self.display_fields(query_set)
        # if query:
        
        #     if param_for_api:
        #         created_articles = fetch_openalex("search=", query.strip().replace(' ', '+'), optional="&per-page=50")
        #         query_set = (self.q_search(query, query_set)
        #                     | query_set.filter(doi__in=created_articles))
        #     else:
        #         query_set = self.q_search(query, query_set)

        # query_set = query_set.order_by(param, 'pk')

        # return query_set

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["name"] = "catalog" 

        return context
    
    def get(self, request, *args, **kwargs):

        query = self.request.GET.get('q')

        if query:
            qs = search_type(query)

            if qs:
                return redirect(
                    reverse("catalog:work_detail", kwargs={'pk': qs})
                )

        return super().get(request, *args, **kwargs)


@method_decorator(cache_page(60 * 15), name="dispatch")    
class WorkDetailView(DetailView, GraphMixin, CitiationMixin):
    model = Artical
    template_name = "work_detail.html"
    slug_field = 'pk'
    slug_url_kwarg = 'pk'
    context_object_name = "article"

    def get_queryset(self):

        query_set =  Artical.objects.prefetch_related(
            Prefetch('articalciteinformation_set', to_attr="articalciteinformation_1"),
            Prefetch('articaldate_set', to_attr="articaldate_1"),
            Prefetch('articalcitedata_set', to_attr="articalcitedata_1"),
            Prefetch('articlemainauthor_set', to_attr="articlemainauthor_1"),
            Prefetch('articleciteperyear_set', 
                     queryset=ArticleCitePerYear.objects.all(),
                     to_attr='citing_per_year'),
            Prefetch('articleotherauthor_set',
                     queryset=ArticleOtherAuthor.objects.all(),
                     to_attr="other_authors"),
        )

        return query_set
        

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["name"] = "Статья"

        article = context["article"]

        context["artical_cite_information"] = article.articalciteinformation_1[0]
        context["artical_date"] = article.articaldate_1[0]
        context["article_main_author"] = article.articlemainauthor_1[0]
        context["artical_cite_data"] = article.articalcitedata_1[0]

        graph = self.graph_create(article)

        cite_types = self.create_cite_data(article, context["artical_date"], context["article_main_author"], context["artical_cite_information"])

        context["graph"] = graph
        context["gost"] = cite_types["GOST"]
        context["mla"] = cite_types["MLA"]

        context["recommendations"] = get_article_recommendations(self.object.pk)

        return context
