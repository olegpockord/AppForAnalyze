from django.contrib import admin

from main.models import Artical, ArticalCiteData, ArticalDate, ArticalCiteInformation

# Register your models here.
admin.site.register(Artical)
admin.site.register(ArticalCiteData)
admin.site.register(ArticalDate)
admin.site.register(ArticalCiteInformation)
