from django.http import HttpResponse
from django.shortcuts import render

from main.models import Artical, ArticalCiteData
from main.utils import fetch_openalex

def test(request):

    query = Artical.objects.filter(doi="10.1038/s41586-020-2649-2")
    
    if not query:
        fetch_openalex("10.1038/s41586-020-2649-2")

    
    return render(request, "main.html", context={})
