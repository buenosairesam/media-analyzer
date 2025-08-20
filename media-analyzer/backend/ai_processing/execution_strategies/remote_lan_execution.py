"""
Remote LAN execution strategy - sends analysis requests to a LAN worker.
"""

import logging
import requests
import base64
import io
from typing import Dict, Any, List
from .base import ExecutionStrategy

logger = logging.getLogger(__name__)


class RemoteLANExecutionStrategy(ExecutionStrategy):
    """Execute analysis on a remote LAN worker via HTTP."""
    
    def __init__(self, worker_host: str, timeout: int = 30):
        self.worker_host = worker_host
        self.timeout = timeout
        
        if not self.worker_host:
            raise ValueError("worker_host is required for RemoteLANExecutionStrategy")
    
    def execute_detection(self, adapter, image, confidence_threshold=0.5) -> List[Dict[str, Any]]:
        """Send detection request to remote LAN worker."""
        try:
            # Encode image for network transfer
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            image_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Determine analysis type from adapter class name
            adapter_name = adapter.__class__.__name__
            if 'Logo' in adapter_name:
                analysis_type = 'logo_detection'
            elif 'Object' in adapter_name:
                analysis_type = 'object_detection'
            elif 'Text' in adapter_name:
                analysis_type = 'text_detection'
            else:
                analysis_type = 'unknown'
            
            # Prepare request payload
            payload = {
                'image': image_b64,
                'analysis_types': [analysis_type],
                'confidence_threshold': confidence_threshold,
                'adapter_config': {
                    'type': adapter_name,
                    'model_identifier': getattr(adapter, 'model_identifier', None)
                }
            }
            
            # Send to LAN worker
            worker_url = f"http://{self.worker_host}"
            if not worker_url.endswith('/ai'):
                worker_url += '/ai'
                
            response = requests.post(
                f"{worker_url}/analyze",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('detections', [])
            
        except requests.exceptions.Timeout:
            logger.error(f"LAN worker timeout after {self.timeout}s")
            return []
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to LAN worker at {self.worker_host}")
            return []
        except Exception as e:
            logger.error(f"Remote LAN execution failed: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if LAN worker is available."""
        try:
            response = requests.get(f"http://{self.worker_host}/ai/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about LAN worker."""
        try:
            response = requests.get(f"http://{self.worker_host}/ai/info", timeout=5)
            if response.status_code == 200:
                worker_info = response.json()
                return {
                    'strategy': 'remote_lan',
                    'status': 'available',
                    'worker_host': self.worker_host,
                    'worker_info': worker_info
                }
        except:
            pass
            
        return {
            'strategy': 'remote_lan',
            'status': 'unavailable',
            'worker_host': self.worker_host,
            'error': 'worker_unreachable'
        }