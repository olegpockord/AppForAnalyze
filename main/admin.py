from django.contrib import admin
from django.db.models import Count
from django.utils import timezone

from main.models import Artical, ArticalCiteData, ArticalDate, ArticalCiteInformation, ArticleCitePerYear, ArticleMainAuthor, ArticleOtherAuthor, ArticalEmbedding, ArticleSearchVector

# Register your models here.
# admin.site.register(Artical)
# admin.site.register(ArticalCiteData)
# admin.site.register(ArticalDate)
# admin.site.register(ArticalCiteInformation)
# admin.site.register(ArticleCitePerYear)
# admin.site.register(ArticleMainAuthor)
# admin.site.register(ArticleOtherAuthor)
# admin.site.register(ArticleSearchVector)

class TemplateSetFilter(admin.SimpleListFilter):
    title = None
    parameter_name = "status"
    field_name = None

    def lookups(self, request, model_admin):
        return [
            ('set', 'Set'),
            ('empty', 'Empty')
        ]

    def queryset(self, request, queryset):
        if self.value() == "set":
            return queryset.filter(**{f"{self.field_name}__isnull": False})
        elif self.value() == "empty":
            return queryset.filter(**{f"{self.field_name}__isnull": True})

class SearchVectorSetFilter(TemplateSetFilter):
    title = "Search vector status"
    field_name = "search_vector"

class EmbeddingSetFilter(TemplateSetFilter):
    title = "Embedding status"
    field_name = "embedding"

class CitiationPerYearFilter(admin.SimpleListFilter):
    title = "Graph info"
    parameter_name = "graph_records"

    def lookups(self, request, model_admin):
        return [
            ('zero', 'No records at all'),
            ('year', 'Have records this year'),
            ('5', 'More than 5 records'),
            ('10', 'More than 10 records'),
        ]

    def queryset(self, request, queryset):

        if self.value() == "year":
            current_year = timezone.now().year
            this_year_ids = ArticleCitePerYear.objects.filter(year=current_year).values_list('article__id', flat=True)

            return queryset.filter(id__in=this_year_ids or [])

        qs = queryset.annotate(records=Count("articleciteperyear"))

        if self.value() == "zero":
            return qs.filter(records=0)

        if self.value():
            return qs.filter(records__gte=int(self.value()))        
     
        
        
class OtherAuthorFilter(admin.SimpleListFilter):
    title = "Other authors quantity"
    parameter_name = "quantity"

    def lookups(self, request, model_admin):
        return [
            ('0', 'No authors'),
            ('1', 'One author'),
            ('2', 'Two authors'),
            ('three', 'Three or more authors'),
        ]

    def queryset(self, request, queryset):
        qs = queryset.annotate(records=Count("articleotherauthor"))

        if self.value() == "three":
            return qs.filter(records__gte=3)

        if self.value():
            return qs.filter(records=int(self.value()))


class ArticalDateInline(admin.TabularInline):
    model = ArticalDate
    fields = (
        'article',
        'date_of_artical',
        'date_of_last_update',
        'date_of_creation',
    )
    readonly_fields = ('date_of_last_update', 'date_of_creation', 'date_of_artical')

    extra = 0

class ArticalCiteDataInline(admin.TabularInline):
    model = ArticalCiteData

    extra = 0

class ArticalCiteInformationInline(admin.TabularInline):
    model = ArticalCiteInformation

    extra = 0

class ArticleCitePerYearInline(admin.TabularInline):
    model = ArticleCitePerYear

    extra = 0

class ArticleMainAuthorInline(admin.TabularInline):
    model = ArticleMainAuthor

    extra = 0

class ArticleOtherAuthorInline(admin.TabularInline):
    model = ArticleOtherAuthor

    extra = 0

class ArticalEmbeddingInline(admin.TabularInline):
    model = ArticalEmbedding
    fields = (
        "article",
        "is_set",
        "abstract_text",
        "embedding",
    )
    readonly_fields = ("is_set",)

    @admin.display(description="Embedding computed", boolean=True)
    def is_set(self, obj):
        field = obj.embedding

        if field is None:
            return False
        
        return True

    extra = 0

class ArticleSearchVectorInline(admin.TabularInline):
    model = ArticleSearchVector
    fields = (
        "article",
        "is_set",
        "search_vector"
    )
    readonly_fields = ("is_set", )

    @admin.display(description="Search vector computed", boolean=True)
    def is_set(self, obj):
        field = obj.search_vector

        if field:
            return True

        return False

    extra = 0

@admin.register(Artical)
class ArticalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "doi",
    )
    list_display_links = ("id", "title")
    fields = (
        "id",
        "title",
        "doi",
        ("issn", "isbn"),
        ("pmid", "mag"),
        "source"
    )
    list_filter = [CitiationPerYearFilter, OtherAuthorFilter, "source",]
    search_fields = ("id", "title", "doi__startswith")
    readonly_fields = ("id", "doi", "source")
    inlines = [ArticalDateInline,
               ArticalCiteDataInline, 
               ArticalCiteInformationInline, 
               ArticleCitePerYearInline, 
               ArticleMainAuthorInline, 
               ArticleOtherAuthorInline,
               ArticalEmbeddingInline,
               ArticleSearchVectorInline]

@admin.register(ArticalDate)
class ArticalDateAdmin(admin.ModelAdmin):
    list_display = (
        'article',
        'date_of_artical',
        'date_of_creation',
        'date_of_last_update',
    )
    readonly_fields = ('date_of_last_update', 'date_of_creation', 'date_of_artical')
    list_filter = ('date_of_last_update', 'date_of_creation', 'date_of_artical')

@admin.register(ArticalCiteData)
class ArticalCiteDataAdmin(admin.ModelAdmin):
    list_display = (
        "article",
        "reference_count",
        "reference_in_work",
    )
    search_fields = ("article__pk",)

@admin.register(ArticalCiteInformation)
class ArticalCiteInformationAdmin(admin.ModelAdmin):
    list_display = (
        "article",
        "journal_name"
    )
    search_fields = ("article__pk", "journal_name")


@admin.register(ArticleCitePerYear)
class ArticleCitePerYearAdmin(admin.ModelAdmin):
    list_display = (
        "article",
        "year",
        "citiation",
    )
    search_fields = ("article__pk",)

@admin.register(ArticleMainAuthor)
class ArticleMainAuthorAdmin(admin.ModelAdmin):
    list_display = (
        "article",
        "main_initials",
    )
    search_fields = ("article__pk", "main_initials")

@admin.register(ArticleOtherAuthor)
class ArticleOtherAuthorAdmin(admin.ModelAdmin):
    list_display = (
        "article",
        "other_initials",
    )
    search_fields = ("article__pk", "other_initials")

@admin.register(ArticalEmbedding)
class ArticalEmbeddingAdmin(admin.ModelAdmin):
    list_display = (
        "article",
        "is_set",
        "pk",
    )
    search_fields = ("article__pk",)
    list_filter = [EmbeddingSetFilter,]

    @admin.display(description="Set", boolean=True)
    def is_set(self, obj):
        field = obj.embedding

        if field is None:
            return False
        
        return True

@admin.register(ArticleSearchVector)
class ArticleSearchVectorAdmin(admin.ModelAdmin):
    list_display = (
        "article",
        "is_set",
        "pk",
    )
    search_fields = ("article__pk",)
    list_filter = [SearchVectorSetFilter,]

    @admin.display(description="Set", boolean=True)
    def is_set(self, obj):
        field = obj.search_vector

        if field:
            return True

        return False