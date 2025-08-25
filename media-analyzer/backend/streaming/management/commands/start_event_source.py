"""
Django management command to start the configured event source.
Supports pluggable event sources: file watcher, cloud storage, webhook, etc.
"""
import signal
import sys
import logging
from django.core.management.base import BaseCommand
from streaming.event_source_manager import get_event_source_manager

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start the configured segment event source (file watcher, cloud events, etc.)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--source-type',
            type=str,
            help='Override event source type (filewatcher, cloud, webhook)'
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show current event source status and exit'
        )
        
    def handle(self, *args, **options):
        # Just show status if requested
        if options['status']:
            self.show_status()
            return
        
        # Initialize event source manager
        try:
            if options['source_type']:
                from streaming.event_source_manager import EventSourceManager
                manager = EventSourceManager(source_type=options['source_type'])
            else:
                manager = get_event_source_manager()
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to initialize event source: {e}'))
            sys.exit(1)
        
        # Show initial status
        status = manager.get_status()
        self.stdout.write(self.style.SUCCESS(
            f"Initialized event source: {status['configured_type']}"
        ))
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            self.stdout.write(self.style.WARNING('Received shutdown signal, stopping event source...'))
            try:
                manager.stop_monitoring()
                self.stdout.write(self.style.SUCCESS('Event source stopped successfully'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error stopping event source: {e}'))
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start monitoring
        try:
            success = manager.start_monitoring()
            if not success:
                self.stdout.write(self.style.ERROR('Failed to start event source monitoring'))
                sys.exit(1)
                
            self.stdout.write(self.style.SUCCESS(
                f"Event source monitoring started successfully with {status['configured_type']}"
            ))
            
            # Keep the command running
            signal.pause()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error starting event source: {e}'))
            try:
                manager.stop_monitoring()
            except:
                pass
            sys.exit(1)
    
    def show_status(self):
        """Show current event source status"""
        try:
            manager = get_event_source_manager()
            status = manager.get_status()
            
            self.stdout.write(self.style.HTTP_INFO('=== Event Source Status ==='))
            self.stdout.write(f"Configured Type: {status['configured_type']}")
            self.stdout.write(f"Initialized: {status['initialized']}")
            
            if status['initialized']:
                source_info = status['source_info']
                self.stdout.write(f"Source Name: {source_info['name']}")
                self.stdout.write(f"Source Type: {source_info['type']}")
                self.stdout.write(f"Status: {source_info['status']}")
                
                # Show source-specific info
                if 'media_dir' in source_info:
                    self.stdout.write(f"Media Directory: {source_info['media_dir']}")
                    self.stdout.write(f"Poll Interval: {source_info['poll_interval']}s")
                    self.stdout.write(f"Processed Files: {source_info['processed_files']}")
                elif 'bucket_name' in source_info:
                    self.stdout.write(f"Bucket Name: {source_info['bucket_name']}")
                elif 'webhook_port' in source_info:
                    self.stdout.write(f"Webhook Port: {source_info['webhook_port']}")
            else:
                self.stdout.write(self.style.ERROR(f"Error: {status.get('error', 'Unknown error')}"))
            
            self.stdout.write(f"Available Types: {', '.join(status['available_types'])}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting status: {e}'))