"""
Cloud execution strategy - uses cloud services or runs cloud-optimized adapters.
"""

import logging
from typing import Dict, Any, List
from .base import ExecutionStrategy

logger = logging.getLogger(__name__)


class CloudExecutionStrategy(ExecutionStrategy):
    """Execute analysis using cloud services (currently wraps existing cloud adapters)."""
    
    def execute_detection(self, adapter, image, confidence_threshold=0.5) -> List[Dict[str, Any]]:
        """Execute detection using cloud-optimized approach."""
        try:
            # For now, use existing cloud adapters directly
            # Could be extended to route to cloud-hosted inference endpoints
            return adapter.detect(image, confidence_threshold)
        except Exception as e:
            logger.error(f"Cloud execution failed: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if cloud services are available."""
        try:
            # Basic credential check for GCP
            import os
            return bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
        except:
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about cloud execution."""
        try:
            import os
            creds_available = bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
            
            info = {
                'strategy': 'cloud',
                'status': 'available' if creds_available else 'unavailable',
                'services': ['google_cloud_vision']
            }
            
            if not creds_available:
                info['error'] = 'credentials_not_configured'
                
            return info
        except Exception as e:
            return {
                'strategy': 'cloud',
                'status': 'error',
                'error': str(e)
            }