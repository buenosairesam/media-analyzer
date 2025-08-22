from celery import shared_task
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .analysis_engine import AnalysisEngine
from .models import VideoAnalysis, DetectionResult, VisualAnalysis, ProcessingQueue, AnalysisProvider
from .config_manager import config_manager

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


@shared_task(bind=True, queue='logo_detection')
def analyze_logo_detection(self, stream_key, segment_path):
    """Dedicated task for logo detection analysis"""
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

        # Check if logo detection is configured
        if not config_manager.has_capability('logo_detection'):
            logger.error("No logo detection provider configured")
            if queue_item:
                queue_item.status = 'failed'
                queue_item.error_message = 'No logo detection provider configured'
                queue_item.save()
            return {"error": "No logo detection provider configured"}
        
        # Initialize analysis engine with cached config
        engine = AnalysisEngine()
        logo_config = config_manager.get_provider_config('logo_detection')
        engine.configure_providers({'logo_detection': logo_config})
        
        # Extract and analyze frame
        frame = engine.extract_frame_from_segment(segment_path)
        if not frame:
            logger.error(f"Failed to extract frame from {segment_path}")
            if queue_item:
                queue_item.status = 'failed'
                queue_item.error_message = 'Failed to extract frame from segment'
                queue_item.save()
            return {"error": "Failed to extract frame"}
        
        # Analyze for logos only - use configured threshold
        from django.conf import settings
        confidence = settings.LOGO_DETECTION_CONFIG['confidence_threshold']
        analysis_results = engine.analyze_frame(frame, ['logo_detection'], confidence_threshold=confidence)
        
        # Store results
        provider_info = config_manager.get_provider_by_type(logo_config['provider_type'])
        provider = AnalysisProvider.objects.get(id=provider_info['id'])
        
        analysis = VideoAnalysis.objects.create(
            stream_key=stream_key,
            segment_path=segment_path,
            provider=provider,
            analysis_type='logo_detection',
            frame_timestamp=0.0,
            confidence_threshold=confidence
        )
        
        detections = []
        if 'logos' in analysis_results:
            for logo in analysis_results['logos']:
                detection = DetectionResult.objects.create(
                    analysis=analysis,
                    label=logo['label'],
                    confidence=logo['confidence'],
                    bbox_x=logo['bbox']['x'],
                    bbox_y=logo['bbox']['y'],
                    bbox_width=logo['bbox']['width'],
                    bbox_height=logo['bbox']['height'],
                    detection_type='logo'
                )
                detections.append(detection.to_dict())
        
        # Send results via WebSocket if detections found
        if detections:
            websocket_group = f"stream_{stream_key}"
            logger.info(f"Sending websocket update to group: {websocket_group}")
            async_to_sync(channel_layer.group_send)(
                websocket_group,
                {
                    "type": "analysis_update",
                    "analysis": analysis.to_dict()
                }
            )
        
        # Update queue status
        if queue_item:
            queue_item.status = 'completed'
            queue_item.save()
        
        result = {
            "detections": len(detections), 
            "analysis_id": str(analysis.id),
            "brands": [d['label'] for d in detections] if detections else []
        }
        return result
        
    except Exception as e:
        logger.error(f"Logo detection failed for {segment_path}: {e}")
        if queue_item:
            queue_item.status = 'failed'
            queue_item.error_message = str(e)
            queue_item.save()
        raise self.retry(countdown=60, max_retries=3)


@shared_task(bind=True, queue='visual_analysis') 
def analyze_visual_properties(self, stream_key, segment_path):
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
def process_video_segment(self, stream_key, segment_path):
    """Main task that dispatches to specialized analysis tasks"""
    try:
        # Dispatch to specialized queues based on available capabilities
        active_capabilities = config_manager.get_active_capabilities()
        
        if 'logo_detection' in active_capabilities:
            analyze_logo_detection.delay(stream_key, segment_path)
        
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