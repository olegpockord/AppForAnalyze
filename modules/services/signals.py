# from django.db.models.signals import post_save
# from django.dispatch import receiver

# from main.models import ArticalEmbedding
# from modules.tasks import precompute_recommendations

# @receiver(post_save, sender=ArticalEmbedding)
# def generate_recommendations(sender, instance, created, **kwargs):
#     if created and instance.embedding:
#         precompute_recommendations.delay(instance.article.id)
