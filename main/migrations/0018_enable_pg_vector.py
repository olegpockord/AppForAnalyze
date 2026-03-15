from django.db import migrations
from pgvector.django import VectorExtension

class Migration(migrations.Migration):
    dependencies = [
        ('main', '0017_artical_title_trgm_gin_and_more'),
    ]
    operations = [
        VectorExtension(),
    ]