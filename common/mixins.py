from main.models import Artical, ArticalCiteData, ArticalCiteInformation, ArticalDate
from django.core.cache import cache


import io, base64
import matplotlib
import matplotlib.pyplot as plt


class GraphMixin:

    def graph_create(self, article_data_set):

        pk = article_data_set.pk

        citing_per_year_set = article_data_set.citing_per_year

        source = article_data_set.source

        if source == "openalex":
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

    def author_parser(self, main_author, other_authors, sourse):
        
        other_authors_len = len(other_authors)

        main_author = main_author.split()

        if sourse == "openalex":
            main_author = main_author[::-1]

            other_authors = [i.split()[::-1] for i in other_authors] # Проверить


    def create_cite_data(self, artical_info, artical_date_info, artical_main_other, article_data_for_cite):
        title = artical_info.title
        source = artical_info.source

        date = artical_date_info.date_of_artical
        
        journal = article_data_for_cite.journal_name
        pages = article_data_for_cite.pages
        volume = article_data_for_cite.volume
        issue = article_data_for_cite.issue

        main_author = artical_main_other.main_initials

        other_authors = artical_info.other_authors

        other_authors = [i.other_initials for i in other_authors]

        other_authors_len = len(other_authors)

        authors = self.author_parser(main_author, other_authors, source)


        if other_authors_len > 2:
            ... # Если их больше двух, то в цитировании они будут et. al.

        if other_authors_len == 0:
            ... # Если их нету, то и прибавлять нечего, будет влиять на запятую в конце основного автора в конце инициалов


        main_author_len = len(main_author)

        if source == "openalex":
            main_author = main_author[::-1]

            if main_author_len == 3:
                main_author[1], main_author[2] = main_author[2], main_author[1]

        author_gost = f"{main_author[0]} {main_author[1][0:1]}. et. al."
        author_mla = f"{main_author[0]}, {main_author[1]}, et. al."

        if main_author_len == 3:
            author_gost = f"{main_author[0]} {main_author[1][0:1]}. {main_author[2]} et. al."
            author_mla = f"{main_author[0]}, {main_author[1]} {main_author[2]}, et. al."

        elif main_author_len == 4:
            author_gost = f"{main_author[0].capitalize()} {main_author[1].capitalize()} {main_author[2]} {main_author[3][0:1]}. et. al."
            author_mla = f"{main_author[0].capitalize()} {main_author[1].capitalize()} {main_author[2]}, {main_author[3]}, et. al."

        cite_data_set = {}

        check_volume_gost = f"— T.{volume}.—"
        empty_string = ""

        gost_cite = f"{author_gost} {title} //{journal}. — {date.year}. {check_volume_gost if volume else empty_string} {chr(8470)+chr(46)+chr(32)+issue if issue else empty_string} —C. {pages}"
        mla_cite = f"{author_mla} {chr(34)+title+chr(34)} {journal} {volume if volume else empty_string}{chr(46) + issue if issue else empty_string} {chr(40)+str(date.year)+chr(41)}: {pages}"

        cite_data_set = {
            "GOST": gost_cite,
            "MLA": mla_cite,
        }

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