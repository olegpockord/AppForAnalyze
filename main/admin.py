from django.contrib import admin

from main.models import Artical, ArticalCiteData, ArticalDate, ArticalCiteInformation

# Register your models here.
admin.site.register(Artical)
admin.site.register(ArticalCiteData)
# admin.site.register(ArticalDate)
admin.site.register(ArticalCiteInformation)

@admin.register(ArticalDate)
class ArticalDateAdmin(admin.ModelAdmin):
    list_display = ('artical', 'date_of_artical', 'date_of_last_update')
    readonly_fields = ('date_of_last_update',)
