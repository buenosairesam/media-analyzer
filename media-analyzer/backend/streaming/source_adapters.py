from abc import ABC, abstractmethod
import logging
from pathlib import Path
from django.conf import settings
from .models import VideoStream, StreamStatus
from .ffmpeg_handler import ffmpeg_handler

logger = logging.getLogger(__name__)


class VideoSourceAdapter(ABC):
    """Abstract base class for video source adapters"""
    
    def __init__(self, stream: VideoStream):
        self.stream = stream
        self.process = None
        
    @abstractmethod
    def start_processing(self) -> bool:
        """Start processing video from this source"""
        pass
    
    @abstractmethod
    def stop_processing(self) -> bool:
        """Stop processing video from this source"""  
        pass
    
    @abstractmethod
    def get_hls_output_path(self) -> str:
        """Get the output path for HLS playlist"""
        pass
    
    def update_stream_status(self, status: StreamStatus):
        """Update stream status in database"""
        self.stream.status = status
        self.stream.save(update_fields=['status'])


class RTMPSourceAdapter(VideoSourceAdapter):
    """Adapter for RTMP streams (OBS, etc.)"""
    
    def start_processing(self) -> bool:
        try:
            self.update_stream_status(StreamStatus.STARTING)
            
            # Files go directly in media directory
            media_dir = Path(settings.MEDIA_ROOT)
            
            # Build RTMP URL
            rtmp_port = getattr(settings, 'RTMP_PORT', 1935)
            rtmp_url = f"rtmp://localhost:{rtmp_port}/live/{self.stream.stream_key}"
            playlist_path = str(media_dir / f'{self.stream.stream_key}.m3u8')
            
            # Start FFmpeg conversion
            self.process = ffmpeg_handler.rtmp_to_hls(rtmp_url, playlist_path)
            
            # HLS URL is now generated dynamically from settings
            
            self.update_stream_status(StreamStatus.ACTIVE)
            logger.info(f"Started RTMP processing for stream {self.stream.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start RTMP processing: {e}")
            self.update_stream_status(StreamStatus.ERROR)
            return False
    
    def stop_processing(self) -> bool:
        try:
            self.update_stream_status(StreamStatus.STOPPING)
            
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=10)
                
            self.update_stream_status(StreamStatus.INACTIVE)
            logger.info(f"Stopped RTMP processing for stream {self.stream.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop RTMP processing: {e}")
            self.update_stream_status(StreamStatus.ERROR)
            return False
    
    def get_hls_output_path(self) -> str:
        media_dir = Path(settings.MEDIA_ROOT)
        return str(media_dir / f'{self.stream.stream_key}.m3u8')


class FileSourceAdapter(VideoSourceAdapter):
    """Adapter for uploaded video files"""
    
    def start_processing(self) -> bool:
        try:
            self.update_stream_status(StreamStatus.STARTING)
            
            if not self.stream.source_file:
                raise ValueError("No source file provided")
                
            # Files go directly in media directory
            media_dir = Path(settings.MEDIA_ROOT)
            
            playlist_path = str(media_dir / f'{self.stream.stream_key}.m3u8')
            
            # Start FFmpeg conversion
            self.process = ffmpeg_handler.file_to_hls(self.stream.source_file.path, playlist_path)
            
            # HLS URL is now generated dynamically from settings
            
            self.update_stream_status(StreamStatus.ACTIVE)
            logger.info(f"Started file processing for stream {self.stream.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start file processing: {e}")
            self.update_stream_status(StreamStatus.ERROR)
            return False
    
    def stop_processing(self) -> bool:
        # File processing typically completes automatically
        return True
    
    def get_hls_output_path(self) -> str:
        media_dir = Path(settings.MEDIA_ROOT)
        return str(media_dir / f'{self.stream.stream_key}.m3u8')


class SourceAdapterFactory:
    """Factory for creating video source adapters"""
    
    @staticmethod
    def create_adapter(stream: VideoStream) -> VideoSourceAdapter:
        adapters = {
            'rtmp': RTMPSourceAdapter,
            'file': FileSourceAdapter,
        }
        
        adapter_class = adapters.get(stream.source_type)
        if not adapter_class:
            raise ValueError(f"Unsupported source type: {stream.source_type}")
            
        return adapter_class(stream)