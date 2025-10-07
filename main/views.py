from django.http import HttpResponse
from django.shortcuts import render

from main.models import Artical, ArticalCiteData
from main.utils import fetch_crossref, fetch_openalex

def test(request):

    query = Artical.objects.filter(doi="10.1056/NEJMoa2001316".lower())
    print(query)

    if not query:
        fetch_crossref("10.1056/NEJMoa2001316".lower())


    return render(request, "main.html", context={})
