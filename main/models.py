from django.db import models

class Artical(models.Model):
    title = models.CharField(max_length=150, blank=False, null=False, verbose_name="Название")
    doi = models.CharField(unique=True, max_length=100, blank=False, null=False, verbose_name="DOI")
    mag = models.CharField(unique=True, max_length=50, blank=True, null=True, verbose_name="MircoSoftAD")
    pubmed = models.CharField(unique=True, max_length=100, blank=True, null=True, verbose_name="PubMedId")
    issn = models.CharField(unique=True, max_length=50, blank=True, null=True, verbose_name="ISSN")
    isbn = models.CharField(unique=True, max_length=50, blank=True, null=True, verbose_name="ISBN")
    abstract = models.TextField(null=True, blank=True, verbose_name="Аннотация")


    class Meta():
        db_table = "Artical"
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"

    def __str__(self):
        return f"{self.title} - {self.doi}"
    

class ArticalCiteData(models.Model):
    artical = models.ForeignKey(to=Artical, on_delete=models.CASCADE, verbose_name="Статья")
    raw = models.JSONField(blank=True, null=True)
    reference_count = models.IntegerField(max_length=100, blank=False, null=False, verbose_name="Цитирований")
    reference_by_count = models.IntegerField(max_length=1000000, blank=False, null=False, verbose_name="Сколько цитировалась")
    source = models.CharField(max_length=20, blank=False, null=True, verbose_name="Источник")

    class Meta():
        db_table = "ArticalCiteData"
        verbose_name = "Информация о цитировании статьи"
        verbose_name_plural = "Информация о цитировании статей"

    def __str__(self):
        return "{self.artical} - {self.reference_count}"
    
