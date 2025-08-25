import logging
from ..analysis_engine import AnalysisEngine
from ..models import AnalysisProvider, ProcessingQueue
from ..tasks import process_video_segment

logger = logging.getLogger(__name__)


class VideoAnalyzer:
    """Main video analysis coordinator"""
    
    def __init__(self):
        self.engine = AnalysisEngine()
        self.configured = False
    
    def setup_providers(self):
        """Configure analysis engine with active providers"""
        try:
            providers = AnalysisProvider.objects.filter(active=True)
            if not providers.exists():
                # Activate local CLIP as fallback
                clip_provider = AnalysisProvider.objects.filter(
                    provider_type='local_clip'
                ).first()
                if clip_provider:
                    clip_provider.active = True
                    clip_provider.save()
                    providers = [clip_provider]
            
            config = {}
            for provider in providers:
                if 'logo_detection' in provider.capabilities:
                    config['logo_detection'] = {
                        'provider_type': provider.provider_type,
                        'model_identifier': provider.model_identifier
                    }
                if 'object_detection' in provider.capabilities:
                    config['object_detection'] = {
                        'provider_type': provider.provider_type,
                        'model_identifier': provider.model_identifier
                    }
            
            if config:
                self.engine.configure_providers(config)
                self.configured = True
                logger.info(f"Configured providers: {list(config.keys())}")
            else:
                logger.warning("No providers with supported capabilities found")
                
        except Exception as e:
            logger.error(f"Error setting up providers: {e}")
    
    def queue_segment_analysis(self, stream_key, segment_path):
        """Queue video segment for analysis"""
        try:
            # Check if already queued
            existing = ProcessingQueue.objects.filter(
                stream_key=stream_key,
                segment_path=segment_path,
                status__in=['pending', 'processing']
            ).exists()
            
            if existing:
                logger.debug(f"Segment already queued: {segment_path}")
                return False
            
            # Create queue item
            queue_item = ProcessingQueue.objects.create(
                stream_key=stream_key,
                segment_path=segment_path,
                analysis_types=['logo_detection'],
                priority=1
            )
            
            # Trigger async processing
            process_video_segment.delay(stream_key, segment_path)
            
            logger.info(f"Queued segment for analysis: {segment_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error queuing segment: {e}")
            return False
    
    def analyze_frame_sync(self, image, analysis_types=['logo_detection'], confidence_threshold=0.3):
        """Synchronous frame analysis for testing"""
        if not self.configured:
            self.setup_providers()
        
        if not self.configured:
            return {"error": "No providers configured"}
        
        try:
            results = self.engine.analyze_frame(image, analysis_types, confidence_threshold)
            return results
        except Exception as e:
            logger.error(f"Frame analysis error: {e}")
            return {"error": str(e)}