from django.db import models



class Artical(models.Model):
    title = models.CharField(max_length=150, blank=False, verbose_name="Название")
    doi = models.CharField(unique=True, max_length=100, blank=False, null=False, verbose_name="DOI")
    mag = models.CharField(unique=True, max_length=50, blank=True, null=True, verbose_name="MircoSoftAD")
    pubmed = models.CharField(unique=True, max_length=100, blank=True, null=True, verbose_name="PubMedId")
    issn = models.CharField(unique=True, max_length=50, blank=True, null=True, verbose_name="ISSN")
    isbn = models.CharField(unique=True, max_length=50, blank=True, null=True, verbose_name="ISBN")


    class Meta():
        db_table = "Artical"
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"

    def __str__(self):
        return f"{self.pk} {self.title} - {self.doi}"

class ArticalCiteData(models.Model):
    artical = models.ForeignKey(to=Artical, on_delete=models.CASCADE, null=True, verbose_name="Статья")
    raw = models.JSONField(blank=True, null=True)
    reference_count = models.IntegerField(blank=False, null=False, verbose_name="Цитирований")
    reference_by_count = models.IntegerField(blank=False, null=False, verbose_name="Сколько цитировалась")
    source = models.CharField(max_length=20, blank=False, null=True, verbose_name="Источник")

    class Meta():
        db_table = "ArticalCiteData"
        verbose_name = "Информация о цитировании статьи"
        verbose_name_plural = "Информация о цитировании статей"

    def __str__(self):
        return f"{self.artical} - {self.reference_by_count}"

class ArticalDate(models.Model):
    artical = models.ForeignKey(to=Artical, on_delete=models.CASCADE,  null=True, verbose_name="Статья")
    date_of_artical = models.DateField(blank=False, null=False, verbose_name="Дата написания")
    date_of_last_update = models.DateField(auto_now=True, verbose_name="Последняя дата обновления")

    class Meta():
        db_table = "ArticalDate"
        verbose_name = "Информация о дате статьи"
        verbose_name_plural = "Информация о датах статьи"

    def __str__(self):
        return f"{self.artical} - {self.date_of_last_update}"
    
        
class ArticalCiteInformation(models.Model):
    artical = models.ForeignKey(to=Artical, on_delete=models.CASCADE,  null=True, verbose_name="Статья")
    journal_name = models.CharField(max_length=100, blank=False, null=False, verbose_name="Имя журнала")
    pages = models.CharField(max_length=30, blank=True, null=True, verbose_name="Страницы")
    volume = models.CharField(max_length=20, blank=True, null=True, verbose_name="Том")
    author = models.CharField(max_length=50, blank=False, null=False, verbose_name="Автор") # Потом сделать флаг, где авторов больше 1, щас пока их всегда больше 1
    issue = models.CharField(max_length=20, blank=True, null=True, verbose_name="Проблема")

    class Meta():
        db_table = "ArticalCiteInformation"
        verbose_name = "Информация для цитирования статьи"
        verbose_name_plural = "Информация для цитирования статьи"

    def __str__(self):
        return f"{self.artical} - {self.journal_name} - {self.author}"