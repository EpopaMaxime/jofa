"""
Prepare the JOFA platform after MySQL (XAMPP) is running:
  - wait for DB
  - apply migrations
  - seed recommendations / integrations if empty
"""

from __future__ import annotations

import time

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Wait for MySQL, migrate, and seed recommendation data if needed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--retries',
            type=int,
            default=30,
            help='How many times to retry MySQL connection (default: 30)',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=2.0,
            help='Seconds between retries (default: 2)',
        )
        parser.add_argument(
            '--force-seed',
            action='store_true',
            help='Always re-run seed_recommendations',
        )

    def handle(self, *args, **options):
        retries = options['retries']
        delay = options['delay']

        self.stdout.write('Waiting for MySQL...')
        for attempt in range(1, retries + 1):
            try:
                connection.ensure_connection()
                self.stdout.write(self.style.SUCCESS(f'MySQL ready (attempt {attempt}).'))
                break
            except OperationalError as exc:
                self.stdout.write(f'  [{attempt}/{retries}] MySQL not ready: {exc}')
                if attempt == retries:
                    self.stderr.write(
                        self.style.ERROR(
                            'Could not connect to MySQL. Start XAMPP MySQL, then retry.'
                        )
                    )
                    raise SystemExit(1)
                time.sleep(delay)
                connection.close()

        self.stdout.write('Applying migrations...')
        call_command('migrate', interactive=False, verbosity=1)

        from recommendations.models import SkinConcern

        if options['force_seed'] or not SkinConcern.objects.exists():
            self.stdout.write('Seeding recommendations / integrations...')
            call_command('seed_recommendations')
        else:
            self.stdout.write('Seed data already present — skipping (use --force-seed to refresh).')

        try:
            call_command('seed_official_vendor')
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f'Official vendor seed skipped: {exc}'))

        self.stdout.write(self.style.SUCCESS('Platform ready. You can run: python manage.py runserver'))
