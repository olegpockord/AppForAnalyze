from main.models import Artical, ArticalCiteData
from main.utils import set_cache

import io, base64
import matplotlib.pyplot as plt


class GraphMixin:

    def graph_create(self, query):
        pk = query.pk
        cite_data_set = ArticalCiteData.objects.select_related("artical").get(artical_id = pk)

        source = cite_data_set.source
        json = cite_data_set.raw

        if source == "openalex":
            citiation_by_years = json["counts_by_year"]

            quantity_of_citiations = len(citiation_by_years)

            years = [citiation_by_years[i]['year'] for i in range(quantity_of_citiations)]
            citiations = [citiation_by_years[i]['cited_by_count'] for i in range(quantity_of_citiations)]

            return self.graph_visual(years, citiations, pk)
        else:
            return None


        

    def graph_visual(self, years, citiations, primary_key):
        cache_key = f"gpaphNo-{primary_key}"
        
        buf = io.BytesIO()

        plt.figure(figsize=(7,4))
        plt.plot(years, citiations, marker='o', markersize=6, markerfacecolor="red")

        for i, (xi, yi) in enumerate(zip(years, citiations)):
            plt.annotate(f'({yi})', (xi, yi),
                        xytext=(-15, 5), textcoords='offset points')

        plt.grid(True)
        plt.xlabel("Года")
        plt.ylabel("Цитирований")
        plt.xlim(years[-1] - 1, years[0] + 1)

        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        buf.seek(0)
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')

        return b64