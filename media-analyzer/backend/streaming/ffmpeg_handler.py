import ffmpeg
import logging
import subprocess
import platform
from pathlib import Path

logger = logging.getLogger(__name__)

class FFmpegHandler:
    """FFmpeg operations using ffmpeg-python library"""
    
    def rtmp_to_hls(self, rtmp_url: str, output_path: str) -> subprocess.Popen:
        """Convert RTMP stream to HLS"""
        stream = ffmpeg.input(rtmp_url)
        output = ffmpeg.output(
            stream, output_path,
            c='copy',  # Copy codecs for speed
            f='hls',
            hls_time=4,
            hls_list_size=10,
            hls_flags='delete_segments'
        )
        return ffmpeg.run_async(output, pipe_stdout=True, pipe_stderr=True)
    
    def file_to_hls(self, input_file: str, output_path: str) -> subprocess.Popen:
        """Convert file to HLS"""
        stream = ffmpeg.input(input_file)
        output = ffmpeg.output(
            stream, output_path,
            c='copy',
            f='hls', 
            hls_time=4
        )
        return ffmpeg.run_async(output, pipe_stdout=True, pipe_stderr=True)
    
    def webcam_to_hls(self, device_index: int, output_path: str, width: int = 640, height: int = 480, fps: int = 30) -> subprocess.Popen:
        """Convert webcam stream to HLS (cross-platform)"""
        system = platform.system().lower()
        
        if system == 'windows':
            # Windows: DirectShow
            stream = ffmpeg.input(
                f'video="Integrated Camera"',
                f='dshow',
                video_size=f'{width}x{height}',
                framerate=fps
            )
        elif system == 'darwin':  # macOS
            # macOS: AVFoundation
            stream = ffmpeg.input(
                f'{device_index}',
                f='avfoundation',
                video_size=f'{width}x{height}',
                framerate=fps
            )
        else:  # Linux and others
            # Linux: Video4Linux2
            stream = ffmpeg.input(
                f'/dev/video{device_index}',
                f='v4l2',
                s=f'{width}x{height}',
                framerate=fps
            )
        
        output = ffmpeg.output(
            stream, output_path,
            vcodec='libx264',
            preset='ultrafast',  # Fast encoding for real-time
            tune='zerolatency',  # Low latency
            f='hls',
            hls_time=2,          # Short segments for responsiveness
            hls_list_size=10,
            hls_flags='delete_segments'
        )
        return ffmpeg.run_async(output, pipe_stdout=True, pipe_stderr=True)

# Singleton
ffmpeg_handler = FFmpegHandler()