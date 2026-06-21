"""
URL configuration for AppForAnalyze project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from AppForAnalyze.settings import DEBUG
from django.conf.urls.i18n import i18n_patterns


urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('api/', include('citation_api.urls', namespace='api')),
]

urlpatterns += i18n_patterns(
    path('', include('main.urls', namespace='main')),
    path('catalog/', include('catalog.urls', namespace='catalog')),
)

if DEBUG:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls")),]


# old paths
# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', include('main.urls', namespace='main')),
#     path('catalog/', include('catalog.urls', namespace='catalog')),
# ]