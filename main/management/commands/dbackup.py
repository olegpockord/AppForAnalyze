from django.core.management import BaseCommand
from django.core.management import call_command
from datetime import datetime

class Command(BaseCommand):

    def handle(self, *args, **options):
        fname = f'database-{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.json'
        self.stdout.write(f'Writing dump to {fname} (utf-8)...')
        
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
        self.stdout.write(self.style.SUCCESS(f'Dump saved to {fname}'))