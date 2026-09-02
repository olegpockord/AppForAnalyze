from django.utils import timezone
from django.core.cache import cache
from django.core.management import call_command
from django.db.models import F, Value
from django.contrib.postgres.search import SearchVector

from main.models import Artical, ArticalDate, ArticalEmbedding, ArticleSearchVector
from common.ml.sentence_transformer_model import get_model
from modules.services.recommendations import get_article_recommendations
from modules.services.service_classes import ArticleUpdateService

from datetime import timedelta
from celery import shared_task
from celery.utils.log import get_task_logger, logging

logger = get_task_logger(__name__)
LOG = logging.getLogger(__name__)


@shared_task
def periodic_update_task():

    three_days_date = timezone.now() - timedelta(days=4)

    queryset_of_articals = ArticalDate.objects.filter(date_of_last_update__lte=three_days_date)
    if not queryset_of_articals:
        return {'status': 'No articals available to update'}

    quantity_articles = len(queryset_of_articals)

    LOG.info(f"Scheduled {quantity_articles} articles for update")
    LOG.info(f"Approximately {(quantity_articles * 55) / 60} minutes for task (1 worker)")

    for i in queryset_of_articals:
        try:
            single_artical_update.delay(i.article.pk)
        except Exception as exc:
            LOG.exception(f"Failed to schedule update_single_article for {i.article.pk}: {exc}")

    return {'status': 'All articles in queue'}


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def single_artical_update(self, article_pk):
    lock_key = f'update_article_lock:{article_pk}'

    got_lock = cache.add(lock_key, '1', timeout=60 * 3)

    if not got_lock:
        LOG.info(f"Article {article_pk} is already being processed by another worker")
        return None
    
    try:
        article = Artical.objects.get(pk=int(article_pk))

        ArticleUpdateService().update(article)

        LOG.info(f"Article was updated: article_pk={article_pk}")
    
    except Artical.DoesNotExist:
        LOG.exception(f"Article not found: article_pk={article_pk}")
        return None
    
    except Exception:
        LOG.exception(f"Unexpected error was occurred: exc={Exception}; article_pk={article_pk}")
        return None

    finally:
        cache.delete(lock_key)


@shared_task()
def create_embedding():
    embedding_set = ArticalEmbedding.objects.filter(embedding__isnull=True)
    success = 0
    
    if not embedding_set.exists():
        LOG.info("No articles available to set embedding")
        return None
    
    model = get_model()
    LOG.info(f"Device used - {model.device}")
    for obj in embedding_set:
        try:
            embedding = model.encode(obj.abstract_text, normalize_embeddings=True).tolist()

            ArticalEmbedding.objects.filter(pk=obj.pk).update(
                embedding=embedding,
            )

            success+=1
        except Exception as exc:
            LOG.exception(f"Failed to set embedding for {obj.article_id}: {exc}")

    LOG.info(f"Quantity of created embeddings: {success}, all amount - {len(embedding_set)}")

    ids_created_embedding = [object.article_id for object in embedding_set]

    return ids_created_embedding


@shared_task
def create_search_vector():
    qs = ArticleSearchVector.objects.filter(search_vector__isnull=True).annotate(
        title=F("article__title"),
        main_author=F("article__articlemainauthor__main_initials")
    )

    if not qs.exists():
        return {'status': 'No articles available to set search vector'}
    
    for obj in qs:
        ArticleSearchVector.objects.filter(pk=obj.pk).update(
            search_vector = SearchVector(Value(obj.title), weight='A')
                            + SearchVector(Value(obj.main_author), weight='B')
        )

    return {'status': f"Quantity of created search vectors: {len(qs)}"}


@shared_task()
def precompute_recommendations(ids_set):
    success = 0

    if not ids_set:
        return {'status': 'No articles avaible to precompute recomendations'}

    try:
        for id in ids_set:
            get_article_recommendations(id)
            success += 1

    except Exception as exc:
        LOG.exception(f"Failed to precompute recommendation for article №{id} due to {exc}")

    return {'status': f"Quantity of precomputed recommendations: {len(ids_set)}, successful - {success}"}

@shared_task
def dbackup_task():
    call_command('dbackup')
