from django.utils import timezone

from main.models import ArticalCiteData, ArticalDate, ArticleCitePerYear

class ArticleUpdater:

    def update_citiations(self, article, data):
        ArticalCiteData.objects.filter(article=article).update(
                reference_count = data["cited_by_count"],
                reference_in_work = data["reference_in_work"],
            )


    def refresh_date_of_last_update(self, article):
        ArticalDate.objects.filter(article=article).update(
                    date_of_last_update = timezone.now()
            )


    def article_delete(self, article):
        try:
            article.delete()
        except Exception as exc:
            ...


    def update_citiations_by_year(self, article, data):

        exist = {i.year: i
                for i in ArticleCitePerYear.objects.filter(article=article)}
        
        to_update = []
        to_create = []
                
        citing_by_years = data.get("citing_by_years")

        if not citing_by_years:
            return None
        
        for i in citing_by_years:

            if i['year'] in exist:
                elem = exist[i['year']]
                elem.citiation = i['cited_by_count']
                to_update.append(elem)
            else:
                article_cite_per_year = ArticleCitePerYear(
                    article = article,
                    year = i['year'],
                    citiation = i['cited_by_count'],
                )
                to_create.append(article_cite_per_year)
                
        ArticleCitePerYear.objects.bulk_create(to_create)
        ArticleCitePerYear.objects.bulk_update(to_update, ["citiation"])