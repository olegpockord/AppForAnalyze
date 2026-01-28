from django.shortcuts import redirect
from django.views.generic import ListView, DetailView
from django.urls import reverse
from django.db.models import Q, OuterRef, Subquery, Prefetch
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from main.models import Artical, ArticalCiteData, ArticalDate, ArticalCiteInformation, ArticleCitePerYear, ArticleMainAuthor, ArticleOtherAuthor

from modules.tasks import periodic_schedule_task
from modules.utils import fetch_openalex, search_type

from common.mixins import CitiationMixin, GraphMixin

from datetime import timedelta
from django.utils import timezone

class CatalogView(ListView):
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

    def get_queryset(self):
        query_set =  Artical.objects.all()

        query_set = query_set.annotate(
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
        
        query = self.request.GET.get('q')
        param_for_api = self.request.GET.get("scope")


        if query:

            query = query.strip().replace(' ', '+')
        
            if param_for_api:
                fetch_openalex("search=", query, optional="&per-page=50")

            query_set = query_set.filter(
            Q(title__icontains=query) |
            Q(articlemainauthor__main_initials__icontains=query)
            )
        
        sort_param = self.request.GET.get("sort")
        param = self.SORT_MAPPING.get(sort_param, 'pk')
           
        query_set = query_set.order_by(param, 'pk')

        return query_set

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

        # periodic_schedule_task.delay() ### Тест

        cite_types = self.create_cite_data(article, context["artical_date"], context["article_main_author"], context["artical_cite_information"])

        context["graph"] = graph
        context["gost"] = cite_types["GOST"]
        context["mla"] = cite_types["MLA"]


        return context
    









# query = self.request.GET.get('q')
        # param_for_api = self.request.GET.get("scope")

        
        # if query:
        #     query_type = search_type(query)
        #     addition = ''

        #     if query_type !=  "search=":
        #         query = query.lower()
        #         filter_kwargs = {f"{query_type[7:-1]}": query}

        #         if not Artical.objects.filter(**filter_kwargs).first():          
        #             fetch_openalex(query_type, query, addition)
        #         return redirect(
        #             reverse("catalog:work_detail", kwargs={'pk': Artical.objects.get(**filter_kwargs).pk})
        #         )
            
        #     addition = "&per-page=50" 
        #     query = query.replace(' ', '+')   

        #     if param_for_api:
        #         print(f"{type} и {addition}")
        #         fetch_openalex(query_type, query, addition)

        #     query_set = query_set.filter(
        #         Q(title__icontains = query) |
        #         Q(articlemainauthor__main_initials__icontains = query)
        #     )

    # def get_query_set(self): # Not correct name, but .first doesnt make new queries

    #     query_set =  Artical.objects.prefetch_related(
    #         Prefetch('articalciteinformation_set', to_attr="articalciteinformation_1"),
    #         Prefetch('articaldate_set', to_attr="articaldate_1"),
    #         Prefetch('articalcitedata_set', to_attr="articalcitedata_1"),
    #         Prefetch('articlemainauthor_set', to_attr="articlemainauthor_1"),
    #         Prefetch('articleciteperyear_set', 
    #                  queryset=ArticleCitePerYear.objects.all(),
    #                  to_attr='citing_per_year'),
    #         'articleotherauthor_set',
    #     )

    #     query_set =  Artical.objects.prefetch_related(
    #         'articalciteinformation_set',
    #         'articaldate_set',
    #         'articalcitedata_set',
    #         'articlemainauthor_set',
    #         Prefetch('articleciteperyear_set', 
    #                  queryset=ArticleCitePerYear.objects.all(),
    #                  to_attr='citing_per_year'),
    #         'articleotherauthor_set',
    #     ).filter(pk = self.kwargs.get(self.slug_url_kwarg))

    #     return query_set