import os
import time
import logging
from pathlib import Path
from django.conf import settings
from ai_processing.processors.video_analyzer import VideoAnalyzer

logger = logging.getLogger(__name__)

class HLSFileWatcher:
    """Watch for new HLS segment files and trigger analysis"""
    
    def __init__(self, media_dir=None, poll_interval=1.0):
        self.media_dir = Path(media_dir or settings.MEDIA_ROOT)
        self.poll_interval = poll_interval
        self.processed_files = set()
        self.analyzer = VideoAnalyzer()
        
    def get_stream_key_from_filename(self, filename):
        """Extract stream_key from filename: 'stream_key-segment_number.ts' -> 'stream_key'"""
        if not filename.endswith('.ts'):
            return None
            
        base_name = filename.rsplit('.', 1)[0]  # Remove .ts extension
        stream_key = base_name.rsplit('-', 1)[0]  # Remove last segment: "-123"
        return stream_key if stream_key else None
    
    def process_new_segment(self, file_path):
        """Process a new HLS segment file"""
        try:
            filename = file_path.name
            stream_key = self.get_stream_key_from_filename(filename)
            
            if stream_key:
                logger.info(f"File watcher: Processing new segment {filename} (stream: {stream_key})")
                self.analyzer.queue_segment_analysis(stream_key, str(file_path))
                logger.info(f"File watcher: Queued segment for analysis: {filename}")
            else:
                logger.warning(f"File watcher: Could not extract stream_key from {filename}")
                
        except Exception as e:
            logger.error(f"File watcher: Error processing {file_path}: {e}")
            import traceback
            logger.error(f"File watcher: Traceback: {traceback.format_exc()}")
    
    def scan_for_new_files(self):
        """Scan for new .ts files in the media directory"""
        try:
            if not self.media_dir.exists():
                return
                
            current_files = set()
            for ts_file in self.media_dir.glob("*.ts"):
                if ts_file.is_file():
                    current_files.add(ts_file)
            
            # Find new files
            new_files = current_files - self.processed_files
            
            for new_file in new_files:
                self.process_new_segment(new_file)
                self.processed_files.add(new_file)
                
        except Exception as e:
            logger.error(f"File watcher: Error scanning directory: {e}")
    
    def start_watching(self):
        """Start the file watching loop"""
        logger.info(f"File watcher: Starting to watch {self.media_dir}")
        
        # Initial scan to catch existing files
        self.scan_for_new_files()
        
        while True:
            try:
                self.scan_for_new_files()
                time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                logger.info("File watcher: Stopped by user")
                break
            except Exception as e:
                logger.error(f"File watcher: Unexpected error: {e}")
                time.sleep(self.poll_interval)