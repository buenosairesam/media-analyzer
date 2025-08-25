from celery import shared_task
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .analysis_engine import AnalysisEngine
from .models import VideoAnalysis, DetectionResult, VisualAnalysis, ProcessingQueue, AnalysisProvider
from .config_manager import config_manager

# Import event_tasks to ensure Celery autodiscovery finds them
from . import event_tasks

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()



@shared_task(bind=True, queue='visual_analysis') 
def analyze_visual_properties(self, stream_key, segment_path, session_id=None):
    """Dedicated task for visual property analysis"""
    queue_item = None
    try:
        # Update queue status
        queue_item = ProcessingQueue.objects.filter(
            stream_key=stream_key, 
            segment_path=segment_path,
            status='pending'
        ).first()
        
        if queue_item:
            queue_item.status = 'processing'  
            queue_item.save()

        # Initialize analysis engine
        engine = AnalysisEngine()
        
        # Extract and analyze frame
        frame = engine.extract_frame_from_segment(segment_path)
        if not frame:
            logger.error(f"Failed to extract frame from {segment_path}")
            if queue_item:
                queue_item.status = 'failed'
                queue_item.error_message = 'Failed to extract frame from segment'
                queue_item.save()
            return {"error": "Failed to extract frame"}
        
        # Analyze visual properties (always available locally)
        analysis_results = engine.analyze_frame(frame, ['visual_analysis'])
        
        # Store results (no provider needed for local visual analysis)
        analysis = VideoAnalysis.objects.create(
            stream_key=stream_key,
            session_id=session_id,
            segment_path=segment_path,
            provider=None,  # Local analysis
            analysis_type='visual_analysis',
            frame_timestamp=0.0,
            confidence_threshold=0.0
        )
        
        # Store visual analysis
        if 'visual' in analysis_results:
            VisualAnalysis.objects.create(
                analysis=analysis,
                dominant_colors=analysis_results['visual']['dominant_colors'],
                brightness_level=analysis_results['visual']['brightness_level'],
                contrast_level=analysis_results['visual']['contrast_level'],
                saturation_level=analysis_results['visual']['saturation_level']
            )
        
        # Send results via WebSocket
        async_to_sync(channel_layer.group_send)(
            f"stream_{stream_key}",
            {
                "type": "analysis_update",
                "analysis": analysis.to_dict()
            }
        )
        
        # Update queue status
        if queue_item:
            queue_item.status = 'completed'
            queue_item.save()
        
        logger.debug(f"Visual analysis completed for {segment_path}")
        return {"analysis_id": str(analysis.id)}
        
    except Exception as e:
        logger.error(f"Visual analysis failed for {segment_path}: {e}")
        if queue_item:
            queue_item.status = 'failed'
            queue_item.error_message = str(e)
            queue_item.save()
        raise self.retry(countdown=60, max_retries=3)


@shared_task(bind=True)
def process_video_segment(self, stream_key, segment_path, session_id=None):
    """Main task that dispatches to specialized analysis tasks"""
    try:
        # Dispatch to specialized queues based on available capabilities
        active_capabilities = config_manager.get_active_capabilities()
        
        # Logo detection now handled by event-driven system in event_tasks.py
        # Events are published by file-watcher and consumed by process_segment_from_event
        
        # Visual analysis disabled for performance - only logo detection
        # analyze_visual_properties.delay(stream_key, segment_path)
        
        return {"dispatched": True, "capabilities": active_capabilities}
        
    except Exception as e:
        logger.error(f"Failed to dispatch analysis for {segment_path}: {e}")
        return {"error": str(e)}


@shared_task(queue='config_management')
def reload_analysis_config():
    """Task to reload analysis provider configuration"""
    try:
        config_manager.reload_config()
        logger.info("Analysis configuration reloaded successfully")
        return {"status": "success", "capabilities": config_manager.get_active_capabilities()}
    except Exception as e:
        logger.error(f"Failed to reload analysis configuration: {e}")
        return {"status": "error", "message": str(e)}


@shared_task
def analyze_frame_task(stream_key, segment_path, frame_timestamp=0.0):
    """Analyze a single frame from video segment"""
    try:
        engine = AnalysisEngine()
        
        # Get active providers
        providers = AnalysisProvider.objects.filter(active=True)
        if not providers.exists():
            return {"error": "No active providers"}
        
        # Configure engine
        config = {}
        for provider in providers:
            if 'logo_detection' in provider.capabilities:
                config['logo_detection'] = {
                    'provider_type': provider.provider_type,
                    'model_identifier': provider.model_identifier
                }
        
        engine.configure_providers(config)
        
        # Extract and analyze frame
        frame = engine.extract_frame_from_segment(segment_path, frame_timestamp)
        if not frame:
            return {"error": "Could not extract frame"}
        
        results = engine.analyze_frame(frame, ['logo_detection', 'visual_analysis'])
        
        return {
            "stream_key": stream_key,
            "results": results,
            "frame_timestamp": frame_timestamp
        }
        
    except Exception as e:
        logger.error(f"Frame analysis error: {e}")
        return {"error": str(e)}