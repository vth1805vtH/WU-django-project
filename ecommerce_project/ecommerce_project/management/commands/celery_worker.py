import subprocess
import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Start the Celery worker. Uses --pool=solo on Windows automatically.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pool', default=None,
            help='Celery pool implementation (e.g. solo, threads, gevent)',
        )
        parser.add_argument(
            '--loglevel', default='info',
            help='Log level (default: info)',
        )
        parser.add_argument(
            'args', nargs='*',
            help='Additional Celery arguments',
        )

    def handle(self, *args, **options):
        cmd = ['celery', '-A', 'ecommerce_project', 'worker']

        pool = options.get('pool')
        if pool is None and sys.platform == 'win32':
            pool = 'solo'

        if pool:
            cmd.extend(['--pool', pool])

        cmd.extend(['--loglevel', options['loglevel']])
        cmd.extend(options.get('args', []))

        self.stdout.write(f'Starting Celery worker: {" ".join(cmd)}')
        try:
            subprocess.run(cmd, check=True)
        except FileNotFoundError:
            self.stderr.write(
                'Celery is not installed or not on PATH. '
                'Run: pip install celery redis'
            )
        except subprocess.CalledProcessError as e:
            self.stderr.write(f'Celery worker exited with code {e.returncode}')
