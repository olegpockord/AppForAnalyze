import re
import uuid

from main.models import Artical
from modules.services.work_flow import ArticleImportWorkFlow
from modules.services.custom_exceptions import SearchSessionExpired

from django.http import Http404
from django.core.cache import cache
from django.utils.translation import gettext as _
from django.contrib import messages


def detect_pattern_type(query):
    doi_pattern = r'^10\.'
    mag_pattern = r'^mag\d'
    pmid_pattern = r'^pmid\d'

    detected = "fts"

    if re.match(doi_pattern, query):
        detected = "doi"

    elif re.match(mag_pattern, query):
        detected = "mag"

    elif re.match(pmid_pattern, query):
        detected = "pmid"

    return detected


def search_type(query):

    identifier = detect_pattern_type(query)

    if identifier == "fts":
        return None
    
    query = query.lower().strip()

    if identifier != "doi":
        first_num_include = re.compile(r'\d')
        first_include_index = re.search(first_num_include, query)
        query = query[first_include_index.start():]

    pattern_kwargs = {identifier: query}
    article = Artical.objects.filter(**pattern_kwargs).first()

    if article:
        return article.pk

    ArticleImportWorkFlow().execute_import(query, identifier)

    new_article = Artical.objects.filter(**pattern_kwargs).first()

    if not new_article:
        raise Http404

    return new_article.pk

def get_openalex_dois(self, query, update_time=180):

    sid = self.request.GET.get("sid")

    if sid:
        dois = cache.get(f"openalex:{sid}")

        if dois is None:
            messages.warning(self.request, _("Время сессии истекло, вы возвращены на главную")) # Session time expired, you returned on main page
            raise SearchSessionExpired

        cache.touch(f"openalex:{sid}", update_time)
        return dois

    created_dois = ArticleImportWorkFlow().execute_import(query.strip().replace(' ', '+'), identifier="fts")

    if not created_dois:
        return None

    sid = uuid.uuid4().hex

    cache.set(f"openalex:{sid}", created_dois, 180)

    self.sid = sid

    return created_dois


