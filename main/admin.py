from django.contrib import admin

from main.models import Artical, ArticalCiteData, ArticalDate, ArticalCiteInformation

# Register your models here.
# admin.site.register(Artical)
# admin.site.register(ArticalCiteData)
# admin.site.register(ArticalDate)
# admin.site.register(ArticalCiteInformation)


class ArticalDateInlive(admin.TabularInline):
    model = ArticalDate
    fields = (
        'artical',
        'date_of_artical',
        'date_of_last_update'
    )
    readonly_fields = ('date_of_last_update',)

    extra = 0

class ArticalCiteDataInlive(admin.TabularInline):
    model = ArticalCiteData

    extra = 0

class ArticalCiteInformationlive(admin.TabularInline):
    model = ArticalCiteInformation

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
        ("pubmed", "mag"),
    )
    list_filter = ("title", "doi")
    search_fields = ("title", "doi", "issn", "pubmed", "mag")
    readonly_fields = ("id",)
    inlines = [ArticalDateInlive, ArticalCiteDataInlive, ArticalCiteInformationlive]



@admin.register(ArticalDate)
class ArticalDateAdmin(admin.ModelAdmin):
    list_display = (
        'artical',
        'date_of_artical',
        'date_of_last_update'
    )
    readonly_fields = ('date_of_last_update',)
    list_filter = ("date_of_artical", "date_of_last_update")

@admin.register(ArticalCiteData)
class ArticalCiteDataAdmin(admin.ModelAdmin):
    list_display = (
        "artical",
        "reference_count",
        "reference_by_count",
        "source",
    )
    readonly_fields = ("source",)
    list_filter = ("source",)
    search_fields = ("pk",)

@admin.register(ArticalCiteInformation)
class ArticalCiteInformationAdmin(admin.ModelAdmin):
    list_display = (
        "artical",
        "author",
    )
    list_filter = ("author", "pages", "journal_name")
    search_fields = ("pk", "author", "journal_name", "pages",)

