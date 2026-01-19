from django.contrib import admin

from main.models import Artical, ArticalCiteData, ArticalDate, ArticalCiteInformation, ArticleCitePerYear, ArticleMainAuthor, ArticleOtherAuthor

# Register your models here.
# admin.site.register(Artical)
# admin.site.register(ArticalCiteData)
# admin.site.register(ArticalDate)
# admin.site.register(ArticalCiteInformation)
# admin.site.register(ArticleCitePerYear)
# admin.site.register(ArticleMainAuthor)
# admin.site.register(ArticleOtherAuthor)


class ArticalDateInline(admin.TabularInline):
    model = ArticalDate
    fields = (
        'article',
        'date_of_artical',
        'date_of_last_update',
        'date_of_creation',
    )
    readonly_fields = ('date_of_last_update', 'date_of_creation',)

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


@admin.register(Artical)
class ArticalAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "doi",
    )
    fields = (
        "id",
        "title",
        "doi",
        ("issn", "isbn"),
        ("pmid", "mag"),
        'source'
    )
    list_filter = ("title", "doi", "source")
    search_fields = ("title", "doi", "issn", "pmid", "mag")
    readonly_fields = ("id", "source")
    inlines = [ArticalDateInline, ArticalCiteDataInline, ArticalCiteInformationInline, ArticleCitePerYearInline, ArticleMainAuthorInline, ArticleOtherAuthorInline]



@admin.register(ArticalDate)
class ArticalDateAdmin(admin.ModelAdmin):
    list_display = (
        'article',
        'date_of_artical',
        'date_of_last_update',
        'date_of_creation',
    )
    readonly_fields = ('date_of_last_update', 'date_of_creation')
    list_filter = ("date_of_artical", "date_of_last_update", 'date_of_creation')

@admin.register(ArticalCiteData)
class ArticalCiteDataAdmin(admin.ModelAdmin):
    list_display = (
        "article",
        "reference_count",
        "reference_in_work",
    )
    search_fields = ("pk",)

@admin.register(ArticalCiteInformation)
class ArticalCiteInformationAdmin(admin.ModelAdmin):
    list_display = (
        "article",
        "journal_name"
    )
    list_filter = ("pages", "journal_name")
    search_fields = ("pk", "journal_name", "pages",)


@admin.register(ArticleCitePerYear)
class ArticleCitePerYearAdmin(admin.ModelAdmin):
    list_display = (
        "article",
        "year",
        "citiation",
    )
    list_filter = ("year", "citiation")
    search_fields = ("pk", "year")

@admin.register(ArticleMainAuthor)
class ArticleMainAuthorAdmin(admin.ModelAdmin):
    list_display = (
        "article",
        "main_initials",
    )
    search_fields = ("pk", "main_initials")

@admin.register(ArticleOtherAuthor)
class ArticleOtherAuthorAdmin(admin.ModelAdmin):
    list_display = (
        "article",
        "other_initials",
    )
    search_fields = ("pk", "other_initials")
