from main.models import Artical, ArticalCiteData, ArticalCiteInformation, ArticalDate
from django.core.cache import cache


import io, base64
import matplotlib
import matplotlib.pyplot as plt
from nameparser import HumanName
from nameparser.config import CONSTANTS
import copy



class GraphMixin:

    def graph_create(self, article_data_set):

        pk = article_data_set.pk

        citing_per_year_set = article_data_set.citing_per_year

        source = article_data_set.source

        if source == "openalex" and citing_per_year_set:
            years = [i.year for i in citing_per_year_set]
            citiations = [i.citiation for i in citing_per_year_set]

            return self.graph_visual(years, citiations, pk)
        else:
            return None


        

    def graph_visual(self, years, citiations, primary_key):
        cache_key = f"gpaphNo-{primary_key}"

        data = cache.get(cache_key)
        if data:
            return data

        matplotlib.use('agg')
        buf = io.BytesIO()

        plt.figure(figsize=(7,4))
        plt.plot(years, citiations, marker='o', markersize=6, markerfacecolor="red")

        for i, (xi, yi) in enumerate(zip(years, citiations)):
            plt.annotate(f'({yi})', (xi, yi),
                        xytext=(-15, 5), textcoords='offset points')

        plt.grid(True)
        plt.xlabel("Years")
        plt.ylabel("Citations")
        plt.xlim(years[-1] - 1, years[0] + 1)

        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        buf.seek(0)
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        cache.set(cache_key, b64, 600)


        return b64
    
class CitiationMixin:

    C = copy.deepcopy(CONSTANTS)

    def extended_constants(self):

        prefixes = [
            # Arabic / Semitic:
            "al", "al-", "al'", "al shaikh", "al-sheikh", "ibn", "bin", "bint", "ben",
            "abu", "abu-", "ibn al", "bint al", "ibn al-",

            # Urdu / Persian / South Asian connectors and common multiword forms:
            "ur", "ur-", "ur ", "ullah", "ulla", "khan", "khawaja", "khwaja", "zada",
            "zada-", "ullah-", "ulla-", "bhai",

            # South/SE Asian honorific connectors (often part of family-name clusters):
            "bai", "begum", "bibi", "rao", "shah", "ahmed", "singh",

            # Romance / Iberian / Latin:
            "de", "del", "de la", "de las", "de los", "dos", "das", "do", "da", "di",
            "della", "della", "d'", "d’", "du", "des", "de le",

            # Spanish multiword particles:
            "y", "y de", "y del",

            # Dutch / Flemish / Afrikaans:
            "van", "van de", "van der", "van den", "van 't", "vander", "van het",

            # Germanic / Austrian / Swiss:
            "von", "zu", "zum", "zur", "vom", "von der", "von den", "freiherr", "freifrau",

            # French:
            "le", "la", "du", "des", "de la",

            # Celtic / Gaelic:
            "mac", "mc", "o'", "o’", "fitz",

            # Italian:
            "della", "del", "d'", "de'",

            # Portuguese / Brazilian:
            "da", "das", "dos", "do", "dos santos", "dos Reis",

            # Malay / Indonesian / SE Asia:
            "bin", "binti", "bte", "bte.", "binti-", "bin-",

            # Other multiword/rare but encountered in metadata:
            "af", "al-qahtani", "al qasimi", "al farsi", "al-farsi", "de la cruz", "de la fuente",
            "van de venen", "van den berg", "van berg"
        ]

        for p in set([s.strip().lower() for s in prefixes if s and not s.isspace()]):
            self.C.prefixes.add(p)
        
        suffix_not_acronyms = [
        "jr", "sr", "ii", "iii", "iv", "v", "esq", "qc", "kc", "ret"
        ]
        
        for s in suffix_not_acronyms:
            self.C.suffix_not_acronyms.add(s)
        
        cap_exceptions = {
        # Romance / Dutch / Germanic
        "de": "de",
        "del": "del",
        "de la": "de la",
        "de los": "de los",
        "van": "van",
        "van der": "van der",
        "van den": "van den",
        "van 't": "van 't",
        "von": "von",
        "zu": "zu",
        "le": "le",
        "la": "la",
        "du": "du",
        "dos": "dos",
        "da": "da",
        "der": "der",
        # Arabic / South Asian
        "al": "al",
        "al-": "al-",
        "ibn": "ibn",
        "bin": "bin",
        "binti": "binti",
        "ur": "ur",
        "ullah": "ullah",
        # Celtic / Gaelic
        "mac": "mac",
        "mc": "mc",
        "o'": "o'",
        }
        self.C.capitalization_exceptions.update(cap_exceptions)

        return self.C
    
    def to_mla_cite(self, human_initials, reversed = False):
        #MLA like type -> Last, first middle. or Last, first.

        last_name = human_initials.last
        first_name = human_initials.first
        middle_name = human_initials.middle

        if middle_name:
            full_mla_name = f"{last_name}, {first_name} {middle_name}."

        else:
            full_mla_name = f"{last_name}, {first_name.rstrip('.')}."


        if reversed:
            if middle_name:
                full_mla_name = f"{middle_name} {first_name} {last_name}"
            else:
                full_mla_name = f"{first_name} {last_name}"

        return full_mla_name



    def to_gost_cite(self, human_initials):
        #GOST like type -> Last first[0]. middle[0]. or Last first[0].
        
        last_name = human_initials.last
        first_name = human_initials.first
        middle_name = human_initials.middle

        if middle_name:
            full_gost_name = f"{last_name} {first_name[0]}. {human_initials.middle[0]}."
        else:
            full_gost_name = f"{last_name} {first_name[0]}."

        return full_gost_name


    def author_parser(self, main_author, other_authors):
        C = self.extended_constants()


        other_authors_len = len(other_authors)

        author_initials = HumanName(main_author, constants=C)

        main_author_gost_name = self.to_gost_cite(author_initials)
        main_author_mla_name = self.to_mla_cite(author_initials)

        prepared_main_author_mla_name = main_author_mla_name[:-1] if main_author_mla_name.endswith("..") else main_author_mla_name.rstrip('.') # ".." if middle name present

        if other_authors_len == 0:
            return {
                "mla": f"{prepared_main_author_mla_name.rstrip('.')}.",
                "gost": main_author_gost_name,
            }
        
        if other_authors_len > 2:
            return {
                "mla": f"{prepared_main_author_mla_name}, et al.",
                "gost": f"{main_author_gost_name} et al.",
            }

        other_mla_citing = []
        main_author_mla_name = ""

        for x in other_authors:
            author_initials = HumanName(x, constants=C)
            other_author_gost_name = self.to_gost_cite(author_initials)
            main_author_gost_name = f"{main_author_gost_name}, {other_author_gost_name}"
            other_author_mla_name = self.to_mla_cite(author_initials, reversed=True)
            other_mla_citing.insert(0, other_author_mla_name)

        main_author_mla_name = f"{prepared_main_author_mla_name}, and {other_mla_citing[0]}."

        if len(other_mla_citing) > 1:
            main_author_mla_name = f"{prepared_main_author_mla_name}, {other_mla_citing[1]}, and {other_mla_citing[0]}."
        
        return {
            "mla": main_author_mla_name,
            "gost": main_author_gost_name,
        }

            
    def create_cite_data(self, artical_info, artical_date_info, artical_main_other, article_data_for_cite):
        cache_key = f"citeNo-{artical_info.pk}"

        data = cache.get(cache_key)
        if data:
            return data
        
        title = artical_info.title

        date = artical_date_info.date_of_artical
        
        journal = article_data_for_cite.journal_name
        pages = article_data_for_cite.pages
        volume = article_data_for_cite.volume
        issue = article_data_for_cite.issue

        main_author = artical_main_other.main_initials

        other_authors = artical_info.other_authors
        other_authors = [i.other_initials for i in other_authors]

        authors = self.author_parser(main_author, other_authors)

        author_gost = authors["gost"]
        author_mla = authors["mla"]

        cite_data_set = {}

        check_volume_gost = f"— T.{volume}."

        gost_cite = f"{author_gost} {title} //{journal if journal else 'No information found about journal'}. — {date.year}. {check_volume_gost if volume else ''} {'—№. '+issue if issue else ''} —C. {pages}"
        mla_cite = f"{author_mla} {chr(34)+title+chr(34)} {journal if journal else 'No information found about journal'} {volume if volume else ''}{'.' + issue if issue else ''} {chr(40)+str(date.year)+chr(41)}: {pages}"

        cite_data_set = {
            "GOST": gost_cite,
            "MLA": mla_cite,
        }

        cache.set(cache_key, cite_data_set, 600)

        return cite_data_set
    

class CacheMixin:
    def set_get_cache(self, cache_name, query, cache_time):
        data = cache.get(cache_name)

        if not data:
            data = query
            cache.set(cache_name, data, cache_time)

        return data
    






        # pk = artical_set.pk
        # title = artical_set.title

        
        # source = cite_data_set.source
        # date = date_set.date_of_artical
        
        # journal = citing_data_set.journal_name
        # pages = citing_data_set.pages
        # volume = citing_data_set.volume
        # issue = citing_data_set.issue
        # raw_author = citing_data_set.author

        # author = raw_author.split()
        # author_len = len(author)

        # if source == "openalex":
        #     author = author[::-1]

        #     if author_len == 3:
        #         author[1], author[2] = author[2], author[1]

        # author_gost = f"{author[0]} {author[1][0:1]}. et. al."
        # author_mla = f"{author[0]}, {author[1]}, et. al."

        # if author_len == 3:
        #     author_gost = f"{author[0]} {author[1][0:1]}. {author[2]} et. al."
        #     author_mla = f"{author[0]}, {author[1]} {author[2]}, et. al."

        # elif author_len == 4:
        #     author_gost = f"{author[0].capitalize()} {author[1].capitalize()} {author[2]} {author[3][0:1]}. et. al."
        #     author_mla = f"{author[0].capitalize()} {author[1].capitalize()} {author[2]}, {author[3]}, et. al."

        # cite_data_set = {}

        # check_volume_gost = f"— T.{volume}.—"
        # empty_string = ""

        # gost_cite = f"{author_gost} {title} //{journal}. — {date.year}. {check_volume_gost if volume else empty_string} {chr(8470)+chr(46)+chr(32)+issue if issue else empty_string} —C. {pages}"
        # mla_cite = f"{author_mla} {chr(34)+title+chr(34)} {journal} {volume if volume else empty_string}{chr(46) + issue if issue else empty_string} {chr(40)+str(date.year)+chr(41)}: {pages}"

        # cite_data_set = {
        #     "GOST": gost_cite,
        #     "MLA": mla_cite,
        # }