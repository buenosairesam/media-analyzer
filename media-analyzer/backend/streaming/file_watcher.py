import os
import time
import logging
import shutil
from pathlib import Path
from django.conf import settings
from ai_processing.processors.video_analyzer import VideoAnalyzer
from .models import VideoStream, StreamStatus

logger = logging.getLogger(__name__)

class HLSFileWatcher:
    """Watch for new HLS segment files and trigger analysis"""
    
    def __init__(self, media_dir=None, poll_interval=1.0):
        self.media_dir = Path(media_dir or settings.MEDIA_ROOT)
        self.poll_interval = poll_interval
        self.processed_files = set()
        self.analyzer = VideoAnalyzer()
        
        # Create a persistent directory for analysis segments
        self.analysis_dir = self.media_dir / 'analysis_segments'
        self.analysis_dir.mkdir(exist_ok=True)
        
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
            # Determine the active stream from the database
            active_stream = VideoStream.objects.filter(status=StreamStatus.ACTIVE).first()
            if not active_stream:
                logger.warning(f"File watcher: No active stream found, skipping segment {file_path.name}")
                return
            stream_key = active_stream.stream_key
            logger.info(f"File watcher: Processing new segment {file_path.name} (stream: {stream_key})")
            
            # Copy the segment to analysis directory to prevent deletion by nginx
            analysis_file_path = self.analysis_dir / file_path.name
            shutil.copy2(file_path, analysis_file_path)
            logger.debug(f"File watcher: Copied segment to {analysis_file_path}")
            
            # Queue the copied file for analysis
            self.analyzer.queue_segment_analysis(stream_key, str(analysis_file_path))
            logger.info(f"File watcher: Queued segment for analysis: {analysis_file_path.name}")
        except Exception as e:
            logger.error(f"File watcher: Error processing {file_path}: {e}")
            import traceback
            logger.error(f"File watcher: Traceback: {traceback.format_exc()}")
    
    def scan_for_new_files(self):
        """Scan for new .ts files in the media directory"""
        try:
            if not self.media_dir.exists():
                logger.debug(f"File watcher: Media directory {self.media_dir} does not exist")
                return
                
            current_files = set()
            for ts_file in self.media_dir.glob("*.ts"):
                if ts_file.is_file():
                    current_files.add(ts_file)
            
            logger.debug(f"File watcher: Found {len(current_files)} total .ts files, {len(self.processed_files)} already processed")
            
            # Find new files
            new_files = current_files - self.processed_files
            
            if new_files:
                logger.info(f"File watcher: Found {len(new_files)} new files to process")
                
            for new_file in new_files:
                self.process_new_segment(new_file)
                self.processed_files.add(new_file)
                
        except Exception as e:
            logger.error(f"File watcher: Error scanning directory: {e}")
            logger.debug(f"File watcher: Scan exception details: {e}")
    
    def start_watching(self):
        """Start the file watching loop"""
        logger.debug(f"File watcher: Starting to watch {self.media_dir}")
        logger.debug(f"File watcher: Directory exists: {self.media_dir.exists()}")
        
        if self.media_dir.exists():
            existing_files = list(self.media_dir.glob("*.ts"))
            logger.debug(f"File watcher: Found {len(existing_files)} existing .ts files")
        
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
                logger.debug(f"File watcher: Exception traceback: {e}")
                time.sleep(self.poll_interval)