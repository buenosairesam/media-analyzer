"""
Event source manager for dynamic selection and management of segment event sources.
Handles environment-based switching between file watchers, cloud storage, etc.
"""
import os
import logging
from typing import Optional, Dict, Any, Type
from django.conf import settings
from streaming.event_sources import (
    SegmentEventSource,
    FileWatcherEventSource,
    CloudStorageEventSource,
    WebhookEventSource
)

logger = logging.getLogger(__name__)


class EventSourceManager:
    """
    Manages event sources based on environment configuration.
    Provides a single interface for starting/stopping segment monitoring.
    """
    
    # Available event source implementations
    EVENT_SOURCE_CLASSES = {
        'filewatcher': FileWatcherEventSource,
        'filesystem': FileWatcherEventSource,  # Alias
        'cloud': CloudStorageEventSource,
        'gcs': CloudStorageEventSource,        # Alias
        'gcp': CloudStorageEventSource,        # Alias
        'webhook': WebhookEventSource,
        'http': WebhookEventSource,            # Alias
    }
    
    def __init__(self, source_type: Optional[str] = None):
        self.source_type = source_type or self._get_configured_source_type()
        self.current_source: Optional[SegmentEventSource] = None
        self._initialize_source()
    
    def _get_configured_source_type(self) -> str:
        """Get event source type from environment configuration"""
        # Check environment variable first
        env_source = os.getenv('SEGMENT_EVENT_SOURCE', '').lower()
        if env_source in self.EVENT_SOURCE_CLASSES:
            return env_source
        
        # Check Django settings
        settings_source = getattr(settings, 'SEGMENT_EVENT_SOURCE', '').lower()
        if settings_source in self.EVENT_SOURCE_CLASSES:
            return settings_source
        
        # Default to file watcher for local development
        return 'filewatcher'
    
    def _initialize_source(self) -> None:
        """Initialize the configured event source"""
        try:
            source_class = self.EVENT_SOURCE_CLASSES.get(self.source_type)
            if not source_class:
                available = ', '.join(self.EVENT_SOURCE_CLASSES.keys())
                raise ValueError(f"Unknown event source type: {self.source_type}. Available: {available}")
            
            # Initialize with appropriate parameters based on source type
            if self.source_type in ['filewatcher', 'filesystem']:
                media_dir = getattr(settings, 'MEDIA_ROOT', None)
                poll_interval = float(os.getenv('FILE_WATCHER_POLL_INTERVAL', 1.0))
                self.current_source = source_class(media_dir=media_dir, poll_interval=poll_interval)
                
            elif self.source_type in ['cloud', 'gcs', 'gcp']:
                bucket_name = os.getenv('GCS_BUCKET_NAME', 'media-segments')
                self.current_source = source_class(bucket_name=bucket_name)
                
            elif self.source_type in ['webhook', 'http']:
                webhook_port = int(os.getenv('WEBHOOK_PORT', 8001))
                self.current_source = source_class(webhook_port=webhook_port)
                
            else:
                # Fallback - initialize with no parameters
                self.current_source = source_class()
            
            logger.info(f"EventSourceManager: Initialized {self.source_type} event source")
            
        except Exception as e:
            logger.error(f"EventSourceManager: Failed to initialize {self.source_type} source: {e}")
            raise
    
    def start_monitoring(self) -> bool:
        """Start segment monitoring with the configured event source"""
        try:
            if not self.current_source:
                logger.error("EventSourceManager: No event source initialized")
                return False
            
            self.current_source.start_monitoring()
            logger.info(f"EventSourceManager: Started monitoring with {self.source_type} source")
            return True
            
        except Exception as e:
            logger.error(f"EventSourceManager: Failed to start monitoring: {e}")
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop segment monitoring"""
        try:
            if not self.current_source:
                logger.warning("EventSourceManager: No event source to stop")
                return True
            
            self.current_source.stop_monitoring()
            logger.info(f"EventSourceManager: Stopped monitoring with {self.source_type} source")
            return True
            
        except Exception as e:
            logger.error(f"EventSourceManager: Failed to stop monitoring: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current event source status and information"""
        if not self.current_source:
            return {
                'configured_type': self.source_type,
                'initialized': False,
                'error': 'Event source not initialized'
            }
        
        source_info = self.current_source.get_source_info()
        return {
            'configured_type': self.source_type,
            'initialized': True,
            'source_info': source_info,
            'available_types': list(self.EVENT_SOURCE_CLASSES.keys())
        }
    
    def switch_source(self, new_source_type: str) -> bool:
        """Switch to a different event source type"""
        try:
            if new_source_type not in self.EVENT_SOURCE_CLASSES:
                available = ', '.join(self.EVENT_SOURCE_CLASSES.keys())
                logger.error(f"EventSourceManager: Invalid source type {new_source_type}. Available: {available}")
                return False
            
            # Stop current source
            was_monitoring = False
            if self.current_source:
                try:
                    current_info = self.current_source.get_source_info()
                    was_monitoring = current_info.get('status') == 'active'
                    self.stop_monitoring()
                except Exception as e:
                    logger.warning(f"EventSourceManager: Error stopping current source: {e}")
            
            # Switch to new source
            old_source_type = self.source_type
            self.source_type = new_source_type
            self._initialize_source()
            
            # Resume monitoring if it was active
            if was_monitoring:
                self.start_monitoring()
            
            logger.info(f"EventSourceManager: Switched from {old_source_type} to {new_source_type}")
            return True
            
        except Exception as e:
            logger.error(f"EventSourceManager: Failed to switch to {new_source_type}: {e}")
            return False
    
    def emit_manual_event(self, segment_path: str, stream_key: str, 
                         session_id: Optional[str] = None) -> bool:
        """Manually emit a segment event (for testing/debugging)"""
        try:
            if not self.current_source:
                logger.error("EventSourceManager: No event source available for manual event")
                return False
            
            success = self.current_source.emit_segment_event(
                segment_path=segment_path,
                stream_key=stream_key,
                session_id=session_id,
                metadata={'manual': True}
            )
            
            if success:
                logger.info(f"EventSourceManager: Manual event emitted for {segment_path}")
            else:
                logger.error(f"EventSourceManager: Failed to emit manual event for {segment_path}")
                
            return success
            
        except Exception as e:
            logger.error(f"EventSourceManager: Error emitting manual event: {e}")
            return False


# Global event source manager instance
_global_event_source_manager: Optional[EventSourceManager] = None


def get_event_source_manager() -> EventSourceManager:
    """Get or create the global event source manager instance"""
    global _global_event_source_manager
    
    if _global_event_source_manager is None:
        _global_event_source_manager = EventSourceManager()
    
    return _global_event_source_manager


def start_segment_monitoring() -> bool:
    """Convenience function to start segment monitoring"""
    manager = get_event_source_manager()
    return manager.start_monitoring()


def stop_segment_monitoring() -> bool:
    """Convenience function to stop segment monitoring"""
    manager = get_event_source_manager()
    return manager.stop_monitoring()


def get_monitoring_status() -> Dict[str, Any]:
    """Convenience function to get monitoring status"""
    manager = get_event_source_manager()
    return manager.get_status()