from abc import ABC, abstractmethod


class DetectionAdapter(ABC):
    """Base class for detection adapters (image-based analysis)"""
    
    @abstractmethod
    def detect(self, image, confidence_threshold=0.5):
        """
        Detect features in image
        
        Returns: List of detection results
        [{'label': str, 'confidence': float, 'bbox': {'x': float, 'y': float, 'width': float, 'height': float}}]
        """
        pass


class VideoAnalysisAdapter(ABC):
    """Base class for video analysis adapters (temporal analysis)"""
    
    @abstractmethod
    def analyze(self, video_path, **kwargs):
        """
        Analyze video for temporal features
        
        Returns: Dict of analysis results
        """
        pass


class AdapterFactory(ABC):
    """Base factory for creating adapters"""
    
    @staticmethod
    @abstractmethod
    def create(provider_config):
        """Create adapter instance from provider configuration"""
        pass