import ffmpeg
import logging
import subprocess
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

# Singleton
ffmpeg_handler = FFmpegHandler()