from django.db import models



class Artical(models.Model):
    title = models.CharField(max_length=300, blank=False, verbose_name="Название")
    doi = models.CharField(unique=True, max_length=100, blank=False, null=False, verbose_name="DOI")
    mag = models.CharField(unique=True, max_length=50, blank=True, null=True, verbose_name="MircoSoftAG")
    pmid = models.CharField(unique=True, max_length=100, blank=True, null=True, verbose_name="PubMedId")
    issn = models.CharField(max_length=50, blank=True, null=True, verbose_name="ISSN")
    isbn = models.CharField(max_length=50, blank=True, null=True, verbose_name="ISBN")
    source = models.CharField(max_length=20, blank=False, null=True, verbose_name="Источник")

    class Meta():
        db_table = "Artical"
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"

    def __str__(self):
        return f"{self.pk} {self.title}"


class ArticalCiteInformation(models.Model):
    article = models.ForeignKey(to=Artical, on_delete=models.CASCADE,  null=True, verbose_name="Статья")
    journal_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Имя журнала")
    pages = models.CharField(max_length=30, blank=True, null=True, verbose_name="Страницы")
    volume = models.CharField(max_length=20, blank=True, null=True, verbose_name="Том")
    issue = models.CharField(max_length=20, blank=True, null=True, verbose_name="Проблема")

    class Meta():
        db_table = "ArticalCiteInformation"
        verbose_name = "Информация для цитирования статьи"
        verbose_name_plural = "Информация для цитирования статьи"

    def __str__(self):
        return f"Статья №{self.article} - {self.journal_name}"


class ArticalDate(models.Model):
    article = models.ForeignKey(to=Artical, on_delete=models.CASCADE,  null=True, verbose_name="Статья")
    date_of_artical = models.DateField(blank=False, null=False, verbose_name="Дата написания")
    date_of_last_update = models.DateField(auto_now=True, verbose_name="Последняя дата обновления")
    date_of_creation = models.DateField(auto_now_add=True, verbose_name="Дата добавление")

    class Meta():
        db_table = "ArticalDate"
        verbose_name = "Информация о дате статьи"
        verbose_name_plural = "Информация о датах статьи"

    def __str__(self):
        return f"Статья №{self.article} - {self.date_of_last_update} дата добавления: {self.date_of_creation}"


class ArticalCiteData(models.Model):
    article = models.ForeignKey(to=Artical, on_delete=models.CASCADE, null=True, verbose_name="Статья")
    reference_count = models.IntegerField(blank=False, null=False, verbose_name="Цитирований")
    reference_in_work = models.IntegerField(blank=False, null=False, verbose_name="Источников в статье")
    

    class Meta():
        db_table = "ArticalCiteData"
        verbose_name = "Информация о цитировании статьи"
        verbose_name_plural = "Информация о цитированиях статей"

    def __str__(self):
        return f"Статья №{self.article} - {self.reference_count}"


class ArticleCitePerYear(models.Model):
    article = models.ForeignKey(to=Artical, on_delete=models.CASCADE, null=True, verbose_name="Статья")
    year = models.IntegerField(blank=False, null=False, verbose_name="Год")
    citiation = models.IntegerField(blank=False, null=False, verbose_name="Цитирований за год")

    class Meta():
        db_table = "ArticleCitePerYear"
        verbose_name = "Информация о цитировании за год"
        verbose_name_plural = "Информация о цитированиях статей за года"

    def __str__(self):
        return f"Статья №{self.article} {self.year}-{self.citiation}"

        
class ArticleMainAuthor(models.Model):
    article = models.ForeignKey(to=Artical, on_delete=models.CASCADE, null=True, verbose_name="Статья")
    main_initials = models.CharField(max_length=100, blank=False, null=True, verbose_name="Инициалы основного автора")

    class Meta():
        db_table = "ArticleMainAuthor"
        verbose_name = "Инициалы основного автора"
        verbose_name_plural = "Инициалы основных авторов"

    def __str__(self):
        return f"Статья №{self.article} {self.main_initials}"


class ArticleOtherAuthor(models.Model):
    article = models.ForeignKey(to=Artical, on_delete=models.CASCADE, null=True, verbose_name="Статья")
    other_initials = models.CharField(max_length=100, blank=False, null=True, verbose_name="Инициалы дополнительного автора")

    class Meta():
        db_table = "ArticleOtherAuthor"
        verbose_name = "Инициалы дополнительно автора"
        verbose_name_plural = "Инициалы дополнительных авторов"

    def __str__(self):
        return f"Статья №{self.article} {self.other_initials}"