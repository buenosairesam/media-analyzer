"""
Remote AI Worker Client for distributed processing.

Supports multiple deployment modes:
- local: AI processing in same K8s cluster 
- remote-lan: AI processing on LAN GPU machine
- cloud-gpu: AI processing on cloud GPU instances
"""

import requests
import logging
from typing import Dict, Any, Optional
from django.conf import settings
import base64
import io
from PIL import Image

logger = logging.getLogger(__name__)


class RemoteAIWorker:
    """Client for communicating with remote AI processing workers."""
    
    def __init__(self):
        self.mode = getattr(settings, 'AI_PROCESSING_MODE', 'local')
        self.worker_host = getattr(settings, 'AI_WORKER_HOST', 'localhost:8001')
        self.worker_timeout = getattr(settings, 'AI_WORKER_TIMEOUT', 30)
        self.use_gpu = getattr(settings, 'AI_WORKER_GPU_ENABLED', False)
        
        # Build worker URL based on mode
        if self.mode == 'remote-lan':
            self.base_url = f"http://{self.worker_host}/ai"
        elif self.mode == 'cloud-gpu':
            self.base_url = f"https://{self.worker_host}/ai"
        else:
            self.base_url = None  # Use local processing
            
        logger.info(f"AI Worker configured: mode={self.mode}, host={self.worker_host}")
    
    def is_remote(self) -> bool:
        """Check if using remote processing."""
        return self.mode in ['remote-lan', 'cloud-gpu']
    
    def encode_image(self, image_array) -> str:
        """Convert numpy array to base64 for network transfer."""
        image = Image.fromarray(image_array)
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=85)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def analyze_frame_remote(self, frame, analysis_types: list, **kwargs) -> Dict[str, Any]:
        """Send frame to remote worker for analysis."""
        if not self.is_remote():
            raise ValueError("Remote analysis called but worker is in local mode")
            
        try:
            # Prepare request payload
            payload = {
                'image': self.encode_image(frame),
                'analysis_types': analysis_types,
                'confidence_threshold': kwargs.get('confidence_threshold', 0.3),
                'use_gpu': self.use_gpu,
                'metadata': {
                    'timestamp': kwargs.get('timestamp'),
                    'stream_id': kwargs.get('stream_id'),
                }
            }
            
            # Send request to remote worker
            response = requests.post(
                f"{self.base_url}/analyze",
                json=payload,
                timeout=self.worker_timeout,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"Remote analysis completed: {len(result.get('detections', []))} detections")
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"Remote AI worker timeout after {self.worker_timeout}s")
            return {'error': 'worker_timeout', 'detections': []}
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to AI worker at {self.base_url}")
            return {'error': 'worker_unreachable', 'detections': []}
        except Exception as e:
            logger.error(f"Remote AI analysis failed: {e}")
            return {'error': str(e), 'detections': []}
    
    def health_check(self) -> bool:
        """Check if remote worker is healthy."""
        if not self.is_remote():
            return True
            
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            result = response.json()
            return result.get('status') == 'healthy'
        except:
            return False
    
    def get_worker_info(self) -> Dict[str, Any]:
        """Get information about the remote worker."""
        if not self.is_remote():
            return {'mode': 'local', 'gpu_available': False}
            
        try:
            response = requests.get(
                f"{self.base_url}/info",
                timeout=5
            )
            return response.json()
        except:
            return {'error': 'worker_unreachable'}


# Global worker instance
remote_worker = RemoteAIWorker()