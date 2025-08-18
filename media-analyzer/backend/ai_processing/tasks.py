from celery import shared_task
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .analysis_engine import AnalysisEngine
from .models import VideoAnalysis, DetectionResult, VisualAnalysis, ProcessingQueue, AnalysisProvider

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


@shared_task(bind=True)
def process_video_segment(self, stream_id, segment_path):
    """Process a video segment with AI analysis"""
    try:
        # Update queue status
        queue_item = ProcessingQueue.objects.filter(
            stream_id=stream_id, 
            segment_path=segment_path,
            status='pending'
        ).first()
        
        if queue_item:
            queue_item.status = 'processing'
            queue_item.save()

        # Initialize analysis engine
        engine = AnalysisEngine()
        
        # Debug: Check all providers
        all_providers = AnalysisProvider.objects.all()
        logger.info(f"Found {all_providers.count()} total providers:")
        for p in all_providers:
            logger.info(f"  - {p.name}: {p.provider_type} (active: {p.active})")
        
        # Get logo detection provider
        logo_provider = AnalysisProvider.objects.filter(
            provider_type='local_clip'
        ).first()
        
        if not logo_provider:
            logger.error("No CLIP provider found in database at all!")
            if queue_item:
                queue_item.status = 'failed'
                queue_item.error_message = 'No CLIP provider in database'
                queue_item.save()
            return {"error": "No CLIP provider in database"}
        
        logger.info(f"Found CLIP provider: {logo_provider.name} (active: {logo_provider.active})")
        
        if not logo_provider.active:
            logo_provider.active = True
            logo_provider.save()
            logger.info(f"Auto-activated CLIP provider: {logo_provider.name}")
        
        if logo_provider:
            # Configure engine with logo detection
            config = {
                'logo_detection': {
                    'provider_type': 'local_clip',
                    'model_identifier': logo_provider.model_identifier
                }
            }
            logger.info(f"Configuring engine with config: {config}")
            engine.configure_providers(config)
            logger.info("Engine configuration completed")
            
            # Extract frame from segment
            logger.info(f"Extracting frame from: {segment_path}")
            frame = engine.extract_frame_from_segment(segment_path)
            if frame:
                logger.info(f"Frame extracted successfully, size: {frame.size}")
                # Analyze frame for logos
                logger.info("Starting frame analysis...")
                analysis_results = engine.analyze_frame(
                    frame, 
                    ['logo_detection', 'visual_analysis'],
                    confidence_threshold=0.3
                )
                logger.info(f"Analysis results: {analysis_results}")
                
                # Store analysis results
                analysis = VideoAnalysis.objects.create(
                    stream_id=stream_id,
                    segment_path=segment_path,
                    provider=logo_provider,
                    analysis_type='logo_detection',
                    frame_timestamp=0.0,
                    confidence_threshold=0.3
                )
                
                # Store detections
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
                if detections:
                    async_to_sync(channel_layer.group_send)(
                        f"stream_{stream_id}",
                        {
                            "type": "analysis_update",
                            "analysis": analysis.to_dict()
                        }
                    )
                
                # Update queue status
                if queue_item:
                    queue_item.status = 'completed'
                    queue_item.save()
                
                logger.info(f"Processed segment {segment_path}: {len(detections)} detections")
                return {"detections": len(detections), "analysis_id": str(analysis.id)}
            else:
                logger.error("Failed to extract frame from segment")
                if queue_item:
                    queue_item.status = 'failed'
                    queue_item.error_message = 'Failed to extract frame from video segment'
                    queue_item.save()
                return {"error": "Failed to extract frame from segment"}
        
        # No provider configured
        if queue_item:
            queue_item.status = 'failed'
            queue_item.error_message = 'No active AI provider configured'
            queue_item.save()
        
        return {"error": "No AI provider configured"}
        
    except Exception as e:
        logger.error(f"Error processing segment {segment_path}: {e}")
        
        if queue_item:
            queue_item.status = 'failed'
            queue_item.error_message = str(e)
            queue_item.save()
        
        raise self.retry(countdown=60, max_retries=3)


@shared_task
def analyze_frame_task(stream_id, segment_path, frame_timestamp=0.0):
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
            "stream_id": stream_id,
            "results": results,
            "frame_timestamp": frame_timestamp
        }
        
    except Exception as e:
        logger.error(f"Frame analysis error: {e}")
        return {"error": str(e)}