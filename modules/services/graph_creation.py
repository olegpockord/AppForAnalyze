import io, base64
import matplotlib
import matplotlib.pyplot as plt

from django.utils.translation import gettext as _


class GraphFormatter:

    def graph_create(self, article_data_set):
        citing_per_year_set = article_data_set.citing_per_year

        source = article_data_set.source

        if source == "openalex" and citing_per_year_set:

            year_citiations_map = {i.year: i.citiation
                                   for i in citing_per_year_set}

            return self.graph_visual(dict(sorted(year_citiations_map.items(), reverse=True)))
        else:
            return None


    def graph_visual(self, years_citiations_dict):

        years = [year for year in years_citiations_dict.keys()]
        citiations = [citiations for citiations in years_citiations_dict.values()]

        matplotlib.use('agg')
        buf = io.BytesIO()

        plt.figure(figsize=(8,5))
        plt.plot(years, citiations, marker='o', markersize=6, markerfacecolor="red")

        for i, (xi, yi) in enumerate(zip(years, citiations)):
            plt.annotate(f'({yi})', (xi, yi),
                        xytext=(-15, 5), textcoords='offset points')

        plt.grid(True)
        plt.xlabel(_("Год"), fontsize=16) # Years
        plt.ylabel(_("Цитирование"), fontsize=18) # Citations
        plt.xlim(years[-1] - 1, years[0] + 1)
        plt.tick_params(axis='both', which='major', labelsize=11)
        
        plt.subplots_adjust(bottom=0.2)

        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        buf.seek(0)
        b64 = base64.b64encode(buf.getvalue()).decode('ascii')

        return b64