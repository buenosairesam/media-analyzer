from django.core.management.base import BaseCommand
from streaming.file_watcher import HLSFileWatcher


class Command(BaseCommand):
    help = 'Watch for new HLS segment files and trigger analysis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--poll-interval',
            type=float,
            default=1.0,
            help='Polling interval in seconds (default: 1.0)'
        )

    def handle(self, *args, **options):
        poll_interval = options['poll_interval']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting HLS file watcher (poll interval: {poll_interval}s)')
        )
        
        watcher = HLSFileWatcher(poll_interval=poll_interval)
        
        try:
            watcher.start_watching()
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.SUCCESS('HLS file watcher stopped')
            )