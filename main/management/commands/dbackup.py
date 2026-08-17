from django.core.management import BaseCommand
from django.core.management import call_command
from datetime import datetime

from celery.utils.log import get_task_logger, logging

logger = get_task_logger(__name__)
LOG = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        fname = f'db_backups/database-{datetime.now().strftime("%Y-%m-%d-%H")}.json'
        LOG.info(f"Start to backup DB at {datetime.now().strftime("%H-%M")}")
        
        with open(fname, 'w', encoding='utf-8') as f:
            call_command(
                'dumpdata',
                '--natural-foreign',
                '--natural-primary',
                '--exclude=contenttypes',
                '--exclude=admin.logentry',
                '--indent=4',
                stdout=f
            )
        LOG.info(f"Backup done at {datetime.now().strftime("%H-%M")}")