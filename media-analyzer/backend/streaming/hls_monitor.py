import os
import time
import logging
from pathlib import Path
from django.conf import settings
from ai_processing.processors.video_analyzer import VideoAnalyzer

logger = logging.getLogger(__name__)


class HLSSegmentMonitor:
    """Monitor HLS segments and trigger AI analysis"""
    
    def __init__(self):
        self.video_analyzer = VideoAnalyzer()
        self.processed_segments = set()
        self.media_dir = getattr(settings, 'MEDIA_ROOT', '/tmp/media')
        
    def start_monitoring(self, stream_id, check_interval=2):
        """Start monitoring for new segments"""
        logger.info(f"Starting HLS monitoring for stream {stream_id}")
        
        while True:
            try:
                self.check_for_new_segments(stream_id)
                time.sleep(check_interval)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                time.sleep(check_interval)
    
    def check_for_new_segments(self, stream_id):
        """Check for new .ts segments and queue them for analysis"""
        try:
            # Look for .ts files in media directory
            media_path = Path(self.media_dir)
            
            # Find .ts files that match the stream pattern
            pattern = f"*{stream_id}*.ts"
            ts_files = list(media_path.glob(pattern))
            
            if not ts_files:
                # Also check for generic .ts files
                ts_files = list(media_path.glob("*.ts"))
            
            for ts_file in ts_files:
                file_path = str(ts_file)
                
                # Skip if already processed
                if file_path in self.processed_segments:
                    continue
                
                # Check if file is complete (not being written)
                if self.is_file_complete(file_path):
                    logger.info(f"Found new segment: {file_path}")
                    
                    # Queue for analysis
                    success = self.video_analyzer.queue_segment_analysis(stream_id, file_path)
                    
                    if success:
                        self.processed_segments.add(file_path)
                        logger.info(f"Queued segment for analysis: {file_path}")
                    
        except Exception as e:
            logger.error(f"Error checking segments: {e}")
    
    def is_file_complete(self, file_path, stable_time=1):
        """Check if file is stable (not being written)"""
        try:
            stat1 = os.stat(file_path)
            time.sleep(stable_time)
            stat2 = os.stat(file_path)
            
            # File is stable if size and modification time haven't changed
            return stat1.st_size == stat2.st_size and stat1.st_mtime == stat2.st_mtime
            
        except (OSError, FileNotFoundError):
            return False
    
    def trigger_manual_analysis(self, stream_id, segment_path):
        """Manually trigger analysis for a specific segment"""
        return self.video_analyzer.queue_segment_analysis(stream_id, segment_path)