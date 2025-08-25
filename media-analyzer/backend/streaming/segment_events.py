import json
import time
import logging
from typing import Optional
from django.conf import settings
import redis

logger = logging.getLogger(__name__)

class SegmentEventPublisher:
    """Publishes segment events to Redis for processing by Celery workers"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST, 
            port=settings.REDIS_PORT, 
            decode_responses=True
        )
        self.event_key = 'media_analyzer:segment_events'
        
    def publish_segment_event(self, segment_path: str, stream_key: str, session_id: Optional[str] = None):
        """Publish a new segment event to Redis and trigger processing"""
        try:
            event = {
                'segment_path': segment_path,
                'stream_key': stream_key,
                'session_id': session_id,
                'timestamp': time.time(),
                'event_type': 'new_segment'
            }
            
            # Push event to Redis list (FIFO queue)
            result = self.redis_client.lpush(self.event_key, json.dumps(event))
            logger.debug(f"Published segment event: {segment_path} (queue length: {result})")
            
            # Trigger event processing task
            try:
                from ai_processing.event_tasks import process_segment_from_event
                process_segment_from_event.delay()
                logger.debug(f"Triggered event processing for {segment_path}")
            except Exception as task_error:
                logger.warning(f"Failed to trigger event processing task: {task_error}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish segment event for {segment_path}: {e}")
            return False
    
    def get_queue_length(self) -> int:
        """Get current number of pending segment events"""
        try:
            return self.redis_client.llen(self.event_key)
        except Exception as e:
            logger.error(f"Failed to get queue length: {e}")
            return 0

class SegmentEventConsumer:
    """Consumes segment events from Redis for processing"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST, 
            port=settings.REDIS_PORT, 
            decode_responses=True
        )
        self.event_key = 'media_analyzer:segment_events'
        
    def consume_segment_event(self, timeout: int = 1) -> Optional[dict]:
        """Consume next segment event from Redis (blocking)"""
        try:
            # BRPOP blocks until event available or timeout
            result = self.redis_client.brpop(self.event_key, timeout=timeout)
            if result:
                _, event_json = result
                event = json.loads(event_json)
                logger.debug(f"Consumed segment event: {event['segment_path']}")
                return event
            return None
            
        except Exception as e:
            logger.error(f"Failed to consume segment event: {e}")
            return None
    
    def peek_next_event(self) -> Optional[dict]:
        """Peek at next event without consuming it"""
        try:
            event_json = self.redis_client.lindex(self.event_key, -1)  # Last item (FIFO)
            if event_json:
                return json.loads(event_json)
            return None
        except Exception as e:
            logger.error(f"Failed to peek at next event: {e}")
            return None