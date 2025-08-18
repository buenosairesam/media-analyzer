import logging
import threading
from typing import Dict, Optional, Any
from django.core.cache import cache
from .models import AnalysisProvider

logger = logging.getLogger(__name__)


class AnalysisConfigManager:
    """Singleton configuration manager for analysis providers"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._config_cache = {}
            self._providers_cache = {}
            self._cache_key = "analysis_providers_config"
            self._initialized = True
            self.reload_config()
    
    def reload_config(self) -> None:
        """Reload provider configuration from database"""
        try:
            providers = AnalysisProvider.objects.filter(active=True)
            
            # Cache providers by type
            self._providers_cache = {}
            config = {}
            
            for provider in providers:
                self._providers_cache[provider.provider_type] = {
                    'id': provider.id,
                    'name': provider.name,
                    'provider_type': provider.provider_type,
                    'model_identifier': provider.model_identifier,
                    'capabilities': provider.capabilities,
                    'config': provider.api_config,
                    'active': provider.active
                }
                
                # Build analysis type configuration
                for capability in provider.capabilities:
                    config[capability] = {
                        'provider_type': provider.provider_type,
                        'model_identifier': provider.model_identifier,
                        'config': provider.api_config
                    }
            
            self._config_cache = config
            
            # Cache in Django cache for other workers
            cache.set(self._cache_key, {
                'providers': self._providers_cache,
                'config': self._config_cache
            }, timeout=3600)  # 1 hour
            
            logger.info(f"Configuration reloaded: {len(providers)} active providers")
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            # Try to load from cache as fallback
            cached_data = cache.get(self._cache_key)
            if cached_data:
                self._providers_cache = cached_data['providers']
                self._config_cache = cached_data['config']
                logger.info("Loaded configuration from cache as fallback")
    
    def get_provider_config(self, analysis_type: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific analysis type"""
        return self._config_cache.get(analysis_type)
    
    def get_provider_by_type(self, provider_type: str) -> Optional[Dict[str, Any]]:
        """Get provider info by provider type"""
        return self._providers_cache.get(provider_type)
    
    def has_capability(self, analysis_type: str) -> bool:
        """Check if any provider supports the analysis type"""
        return analysis_type in self._config_cache
    
    def get_active_capabilities(self) -> list:
        """Get list of all supported analysis capabilities"""
        return list(self._config_cache.keys())
    
    def get_config_for_engine(self) -> Dict[str, Any]:
        """Get configuration in format expected by AnalysisEngine"""
        return self._config_cache.copy()


# Global instance
config_manager = AnalysisConfigManager()