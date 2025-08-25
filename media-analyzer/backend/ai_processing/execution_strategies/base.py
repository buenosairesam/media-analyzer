"""
Base execution strategy for AI processing.

Execution strategies determine WHERE analysis runs, while adapters determine WHAT analysis to do.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ExecutionStrategy(ABC):
    """Base class for execution strategies."""
    
    @abstractmethod
    def execute_detection(self, adapter, image, confidence_threshold=0.5) -> List[Dict[str, Any]]:
        """Execute detection using provided adapter."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this execution strategy is available/healthy."""
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Get information about this execution strategy."""
        pass


class ExecutionStrategyFactory:
    """Factory for creating execution strategies."""
    
    @staticmethod
    def create(strategy_type: str, **kwargs) -> ExecutionStrategy:
        """Create execution strategy based on type."""
        
        if strategy_type == 'local':
            from .local_execution import LocalExecutionStrategy
            return LocalExecutionStrategy()
        elif strategy_type == 'remote_lan':
            from .remote_lan_execution import RemoteLANExecutionStrategy
            worker_host = kwargs.get('worker_host')
            timeout = kwargs.get('timeout', 30)
            return RemoteLANExecutionStrategy(worker_host, timeout)
        elif strategy_type == 'cloud':
            from .cloud_execution import CloudExecutionStrategy
            return CloudExecutionStrategy()
        else:
            raise ValueError(f"Unknown execution strategy: {strategy_type}")