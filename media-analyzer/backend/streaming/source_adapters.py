from abc import ABC, abstractmethod
import logging
from pathlib import Path
from django.conf import settings
from .models import VideoStream, StreamStatus
from .ffmpeg_handler import ffmpeg_handler
import threading
import os
import signal

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
            
            # Check if any other stream is active (only one stream allowed)
            active_streams = VideoStream.objects.filter(status=StreamStatus.ACTIVE).exclude(id=self.stream.id)
            if active_streams.exists():
                logger.warning(f"Cannot start RTMP - another stream is active: {active_streams.first().name}")
                self.update_stream_status(StreamStatus.ERROR)
                return False
            
            # Files go directly in media directory
            media_dir = Path(settings.MEDIA_ROOT)
            
            # Build RTMP URL
            rtmp_port = getattr(settings, 'RTMP_PORT', 1935)
            rtmp_url = f"rtmp://localhost:{rtmp_port}/live/{self.stream.stream_key}"
            playlist_path = str(media_dir / f'{self.stream.stream_key}.m3u8')
            
            # Start FFmpeg conversion
            self.process = ffmpeg_handler.rtmp_to_hls(rtmp_url, playlist_path)
            # Persist FFmpeg PID for stop operations
            try:
                pid_file = media_dir / f'{self.stream.stream_key}.pid'
                with pid_file.open('w') as f:
                    f.write(str(self.process.pid))
            except Exception as e:
                logger.error(f"RTMPSourceAdapter: Failed to write PID file: {e}")
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
            media_dir = Path(settings.MEDIA_ROOT)
            pid_file = media_dir / f'{self.stream.stream_key}.pid'
            # Attempt to terminate in-memory process
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=10)
                except Exception:
                    pass
            # Fallback: terminate by PID file
            elif pid_file.exists():
                try:
                    pid = int(pid_file.read_text())
                    os.kill(pid, signal.SIGTERM)
                except Exception as kill_err:
                    logger.error(f"RTMPSourceAdapter: Failed to kill PID {pid}: {kill_err}")
            # Cleanup PID file
            if pid_file.exists():
                try:
                    pid_file.unlink()
                except Exception as unlink_err:
                    logger.error(f"RTMPSourceAdapter: Failed to remove PID file: {unlink_err}")
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


class WebcamSourceAdapter(VideoSourceAdapter):
    """Adapter for webcam streams"""
    
    def start_processing(self) -> bool:
        try:
            logger.info(f"Starting webcam processing for stream {self.stream.id} with key {self.stream.stream_key}")
            self.update_stream_status(StreamStatus.STARTING)
            
            # Check if any other stream is active (only one stream allowed)
            active_streams = VideoStream.objects.filter(status=StreamStatus.ACTIVE).exclude(id=self.stream.id)
            if active_streams.exists():
                logger.warning(f"Cannot start webcam - another stream is active: {active_streams.first().name}")
                self.update_stream_status(StreamStatus.ERROR)
                return False
            
            # Files go directly in media directory
            media_dir = Path(settings.MEDIA_ROOT)
            playlist_path = str(media_dir / f'{self.stream.stream_key}.m3u8')
            logger.info(f"Webcam playlist path: {playlist_path}")
            
            # Default to webcam 0
            device_index = 0
            
            # Start FFmpeg conversion
            logger.info(f"Starting FFmpeg webcam conversion with device {device_index}")
            self.process = ffmpeg_handler.webcam_to_hls(device_index, playlist_path)
            
            # Check if FFmpeg process started successfully
            if self.process.poll() is not None:
                # Process already exited - get error details
                try:
                    stdout, stderr = self.process.communicate(timeout=2)
                    error_msg = stderr.decode('utf-8') if stderr else "Unknown FFmpeg error"
                    logger.error(f"FFmpeg failed to start webcam: {error_msg}")
                except Exception as comm_error:
                    logger.error(f"FFmpeg failed and couldn't read error: {comm_error}")
                    error_msg = "FFmpeg process failed to start"
                
                self.update_stream_status(StreamStatus.ERROR)
                raise Exception(f"Webcam initialization failed: {error_msg}")
            
            logger.info(f"FFmpeg process started successfully with PID: {self.process.pid}")
            # Persist FFmpeg PID for stop operations
            try:
                pid_file = media_dir / f'{self.stream.stream_key}.pid'
                with pid_file.open('w') as f:
                    f.write(str(self.process.pid))
            except Exception as e:
                logger.error(f"WebcamSourceAdapter: Failed to write PID file: {e}")
            self.update_stream_status(StreamStatus.ACTIVE)
            logger.info(f"Started webcam processing for stream {self.stream.id}")
            # Monitor FFmpeg process and handle unexpected termination
            threading.Thread(target=self._monitor_webcam, daemon=True).start()
            return True
            
        except Exception as e:
            logger.error(f"Failed to start webcam processing: {e}")
            logger.exception(f"Full exception details:")
            self.update_stream_status(StreamStatus.ERROR)
            return False
    
    def stop_processing(self) -> bool:
        try:
            self.update_stream_status(StreamStatus.STOPPING)
            media_dir = Path(settings.MEDIA_ROOT)
            pid_file = media_dir / f'{self.stream.stream_key}.pid'
            # Attempt to terminate in-memory process
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=10)
                except Exception:
                    pass
            # Fallback: terminate by PID file
            elif pid_file.exists():
                try:
                    pid = int(pid_file.read_text())
                    os.kill(pid, signal.SIGTERM)
                except Exception as kill_err:
                    logger.error(f"WebcamSourceAdapter: Failed to kill PID {pid}: {kill_err}")
            # Cleanup PID file
            if pid_file.exists():
                try:
                    pid_file.unlink()
                except Exception as unlink_err:
                    logger.error(f"WebcamSourceAdapter: Failed to remove PID file: {unlink_err}")
            self.update_stream_status(StreamStatus.INACTIVE)
            logger.info(f"Stopped webcam processing for stream {self.stream.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop webcam processing: {e}")
            self.update_stream_status(StreamStatus.ERROR)
            return False
    
    def get_hls_output_path(self) -> str:
        media_dir = Path(settings.MEDIA_ROOT)
        return str(media_dir / f'{self.stream.stream_key}.m3u8')
    
    def _monitor_webcam(self):
        """Monitor the FFmpeg webcam process and update stream status on exit"""
        try:
            exit_code = self.process.wait()
            if exit_code != 0:
                logger.error(f"FFmpeg webcam process terminated unexpectedly with code {exit_code}")
                new_status = StreamStatus.ERROR
            else:
                logger.info(f"FFmpeg webcam process terminated normally with code {exit_code}")
                new_status = StreamStatus.INACTIVE
            self.update_stream_status(new_status)
        except Exception as e:
            logger.error(f"Error monitoring FFmpeg webcam process: {e}")


class SourceAdapterFactory:
    """Factory for creating video source adapters"""
    
    @staticmethod
    def create_adapter(stream: VideoStream) -> VideoSourceAdapter:
        adapters = {
            'rtmp': RTMPSourceAdapter,
            'file': FileSourceAdapter,
            'webcam': WebcamSourceAdapter,
        }
        
        adapter_class = adapters.get(stream.source_type)
        if not adapter_class:
            raise ValueError(f"Unsupported source type: {stream.source_type}")
            
        return adapter_class(stream)