from django.db import migrations
from django.contrib.postgres.operations import CreateExtension

class Migration(migrations.Migration):
    dependencies = [
        ('main', '0015_rename_pubmed_artical_pmid'),
    ]
    operations = [
        CreateExtension('pg_trgm'),
    ]