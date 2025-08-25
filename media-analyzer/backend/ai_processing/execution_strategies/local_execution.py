"""
Local execution strategy - runs analysis adapters in the same process/container.
"""

import logging
from typing import Dict, Any, List
from .base import ExecutionStrategy

logger = logging.getLogger(__name__)


class LocalExecutionStrategy(ExecutionStrategy):
    """Execute analysis adapters locally in the same process."""
    
    def execute_detection(self, adapter, image, confidence_threshold=0.5) -> List[Dict[str, Any]]:
        """Execute detection using the adapter directly."""
        try:
            return adapter.detect(image, confidence_threshold)
        except Exception as e:
            logger.error(f"Local execution failed: {e}")
            return []
    
    def is_available(self) -> bool:
        """Local execution is always available."""
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about local execution."""
        return {
            'strategy': 'local',
            'status': 'available',
            'location': 'same_container'
        }