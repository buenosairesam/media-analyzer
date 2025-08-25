"""
Event source abstraction for segment monitoring.
Supports file system watchers, cloud storage events, and other sources.
"""
import os
import time
import logging
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class SegmentEventSource(ABC):
    """Abstract base class for segment event sources"""
    
    def __init__(self):
        self.publisher = None
        self._setup_publisher()
    
    def _setup_publisher(self):
        """Initialize the event publisher"""
        try:
            from streaming.segment_events import SegmentEventPublisher
            self.publisher = SegmentEventPublisher()
            logger.info(f"Initialized {self.__class__.__name__} event source")
        except Exception as e:
            logger.error(f"Failed to setup event publisher: {e}")
            raise
    
    @abstractmethod
    def start_monitoring(self) -> None:
        """Start monitoring for new segments - implementation specific"""
        pass
    
    @abstractmethod 
    def stop_monitoring(self) -> None:
        """Stop monitoring - implementation specific"""
        pass
    
    def emit_segment_event(self, segment_path: str, stream_key: str, 
                          session_id: Optional[str] = None, 
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Common event emission logic for all sources.
        This ensures consistent event format regardless of source.
        """
        if not self.publisher:
            logger.error("Event publisher not initialized")
            return False
            
        try:
            # Add source metadata
            if metadata is None:
                metadata = {}
            metadata['source'] = self.__class__.__name__
            
            success = self.publisher.publish_segment_event(
                segment_path=segment_path,
                stream_key=stream_key, 
                session_id=session_id
            )
            
            if success:
                logger.debug(f"Event emitted by {self.__class__.__name__}: {segment_path}")
            else:
                logger.warning(f"Failed to emit event from {self.__class__.__name__}: {segment_path}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error emitting event from {self.__class__.__name__}: {e}")
            return False
    
    def get_source_info(self) -> Dict[str, Any]:
        """Return information about this event source"""
        return {
            'name': self.__class__.__name__,
            'type': 'unknown',
            'status': 'unknown'
        }


class FileWatcherEventSource(SegmentEventSource):
    """File system watcher event source for local development"""
    
    def __init__(self, media_dir: Optional[str] = None, poll_interval: float = 1.0):
        super().__init__()
        self.media_dir = Path(media_dir or settings.MEDIA_ROOT)
        self.poll_interval = poll_interval
        self.processed_files = set()
        self._monitoring = False
        self._monitor_thread = None
        
    def get_stream_key_from_active_stream(self) -> Optional[tuple]:
        """Get active stream info from database"""
        try:
            from streaming.models import VideoStream, StreamStatus
            active_stream = VideoStream.objects.filter(status=StreamStatus.ACTIVE).first()
            if active_stream:
                return active_stream.stream_key, getattr(active_stream, 'session_id', None)
            return None, None
        except Exception as e:
            logger.error(f"FileWatcher: Error getting active stream: {e}")
            return None, None
    
    def process_new_segment(self, file_path: Path) -> None:
        """Process a new HLS segment file by emitting event"""
        try:
            stream_key, session_id = self.get_stream_key_from_active_stream()
            if not stream_key:
                logger.warning(f"FileWatcher: No active stream found, skipping {file_path.name}")
                return
                
            logger.debug(f"FileWatcher: Processing new segment {file_path.name} (stream: {stream_key})")
            
            success = self.emit_segment_event(
                segment_path=str(file_path),
                stream_key=stream_key,
                session_id=session_id
            )
            
            if success:
                logger.debug(f"FileWatcher: Emitted event for {file_path.name}")
            else:
                logger.error(f"FileWatcher: Failed to emit event for {file_path.name}")
                
        except Exception as e:
            logger.error(f"FileWatcher: Error processing {file_path}: {e}")
    
    def scan_for_new_files(self) -> None:
        """Scan for new .ts files in the media directory"""
        try:
            if not self.media_dir.exists():
                logger.debug(f"FileWatcher: Media directory {self.media_dir} does not exist")
                return
                
            current_files = set()
            for ts_file in self.media_dir.glob("*.ts"):
                if ts_file.is_file():
                    current_files.add(ts_file)
            
            # Find new files
            new_files = current_files - self.processed_files
            
            if new_files:
                logger.debug(f"FileWatcher: Found {len(new_files)} new files to process")
                
            for new_file in new_files:
                self.process_new_segment(new_file)
                self.processed_files.add(new_file)
                
        except Exception as e:
            logger.error(f"FileWatcher: Error scanning directory: {e}")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop running in thread"""
        logger.info(f"FileWatcher: Started monitoring {self.media_dir}")
        
        # Initial scan for existing files
        self.scan_for_new_files()
        
        while self._monitoring:
            try:
                self.scan_for_new_files()
                time.sleep(self.poll_interval)
            except Exception as e:
                if self._monitoring:  # Only log if still supposed to be running
                    logger.error(f"FileWatcher: Error in monitor loop: {e}")
                    time.sleep(self.poll_interval)
    
    def start_monitoring(self) -> None:
        """Start file system monitoring in background thread"""
        if self._monitoring:
            logger.warning("FileWatcher: Already monitoring")
            return
            
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info(f"FileWatcher: Started monitoring thread for {self.media_dir}")
    
    def stop_monitoring(self) -> None:
        """Stop file system monitoring"""
        if not self._monitoring:
            return
            
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        logger.info("FileWatcher: Stopped monitoring")
    
    def get_source_info(self) -> Dict[str, Any]:
        """Return file watcher source information"""
        return {
            'name': 'FileWatcherEventSource',
            'type': 'filesystem',
            'status': 'active' if self._monitoring else 'stopped',
            'media_dir': str(self.media_dir),
            'poll_interval': self.poll_interval,
            'processed_files': len(self.processed_files)
        }


class CloudStorageEventSource(SegmentEventSource):
    """Cloud storage event source for production deployments"""
    
    def __init__(self, bucket_name: Optional[str] = None):
        super().__init__()
        self.bucket_name = bucket_name or os.getenv('GCS_BUCKET_NAME', 'media-segments')
        self._monitoring = False
        
    def start_monitoring(self) -> None:
        """Start cloud storage event monitoring"""
        # TODO: Implement GCS Pub/Sub or webhook receiver
        logger.info(f"CloudStorage: Would start monitoring bucket {self.bucket_name}")
        logger.warning("CloudStorage: Not yet implemented - placeholder for future cloud deployment")
        self._monitoring = True
    
    def stop_monitoring(self) -> None:
        """Stop cloud storage event monitoring"""
        logger.info("CloudStorage: Stopping monitoring")
        self._monitoring = False
    
    def get_source_info(self) -> Dict[str, Any]:
        """Return cloud storage source information"""
        return {
            'name': 'CloudStorageEventSource',
            'type': 'cloud_storage',
            'status': 'active' if self._monitoring else 'stopped',
            'bucket_name': self.bucket_name,
            'implementation': 'placeholder'
        }


class WebhookEventSource(SegmentEventSource):
    """Webhook receiver event source for external integrations"""
    
    def __init__(self, webhook_port: int = 8001):
        super().__init__()
        self.webhook_port = webhook_port
        self._monitoring = False
        
    def start_monitoring(self) -> None:
        """Start webhook server"""
        # TODO: Implement webhook HTTP server
        logger.info(f"Webhook: Would start server on port {self.webhook_port}")
        logger.warning("Webhook: Not yet implemented - placeholder for future integrations")
        self._monitoring = True
    
    def stop_monitoring(self) -> None:
        """Stop webhook server"""
        logger.info("Webhook: Stopping server")
        self._monitoring = False
    
    def get_source_info(self) -> Dict[str, Any]:
        """Return webhook source information"""
        return {
            'name': 'WebhookEventSource',
            'type': 'webhook',
            'status': 'active' if self._monitoring else 'stopped',
            'webhook_port': self.webhook_port,
            'implementation': 'placeholder'
        }