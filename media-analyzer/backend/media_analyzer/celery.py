import os
from celery import Celery
from celery.signals import worker_ready
import django
import logging

# Set the default Django settings module for the 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'media_analyzer.settings.development')

app = Celery('media_analyzer')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Initialize configuration when worker starts"""
    import django
    django.setup()
    
    from ai_processing.config_manager import config_manager
    logger = logging.getLogger(__name__)
    
    try:
        config_manager.reload_config()
        capabilities = config_manager.get_active_capabilities()
        logger.info(f"Worker ready - loaded capabilities: {capabilities}")
    except Exception as e:
        logger.error(f"Failed to initialize worker configuration: {e}")

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')