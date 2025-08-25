import os
import logging
from pathlib import Path
from celery import shared_task
from streaming.segment_events import SegmentEventConsumer
from .analysis_engine import AnalysisEngine

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_segment_from_event(self):
    """
    Celery task that consumes segment events from Redis and processes them.
    This replaces the file-watcher copying approach with an event-driven model.
    """
    consumer = SegmentEventConsumer()
    
    try:
        # Consume next segment event (non-blocking with short timeout)
        event = consumer.consume_segment_event(timeout=1)
        
        if not event:
            # No events available, task completes normally
            return {'status': 'no_events', 'processed': 0}
        
        segment_path = event['segment_path']
        stream_key = event['stream_key']
        session_id = event.get('session_id')
        
        logger.info(f"Processing segment event: {segment_path} (stream: {stream_key})")
        
        # Check if segment file still exists (nginx might have rotated it)
        if not Path(segment_path).exists():
            logger.warning(f"Segment file no longer exists: {segment_path} - skipping")
            return {'status': 'file_missing', 'segment_path': segment_path}
        
        # Initialize analysis engine and configure for logo detection
        analysis_engine = AnalysisEngine()
        
        # Configure logo detection provider (using existing config)
        from .config_manager import config_manager
        if not config_manager.has_capability('logo_detection'):
            logger.error("No logo detection provider configured")
            return {'status': 'error', 'error': 'No logo detection provider configured'}
        
        logo_config = config_manager.get_provider_config('logo_detection')
        analysis_engine.configure_providers({'logo_detection': logo_config})
        
        # Extract frame from segment
        frame = analysis_engine.extract_frame_from_segment(segment_path)
        if not frame:
            logger.error(f"Failed to extract frame from {segment_path}")
            return {'status': 'error', 'error': 'Failed to extract frame from segment'}
        
        # Analyze frame for logo detection
        results = analysis_engine.analyze_frame(
            image=frame,
            requested_analysis=['logo_detection'],
            confidence_threshold=0.5
        )
        
        logo_detections = results.get('logos', [])
        logger.info(f"Completed analysis for {segment_path}: {len(logo_detections)} logo detections")
        
        # Store results in database
        from .models import VideoAnalysis, DetectionResult
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        analysis = VideoAnalysis.objects.create(
            stream_key=stream_key,
            session_id=session_id,
            segment_path=segment_path,
            processing_time=1.5,  # Approximate processing time
            analysis_type='logo_detection',
            frame_timestamp=0.0  # First frame of segment
        )
        
        # Create detection records and prepare for WebSocket
        detections = []
        for logo in logo_detections:
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
        
        # Send results via WebSocket (always send, even with 0 detections)
        channel_layer = get_channel_layer()
        websocket_group = f"stream_{stream_key}"
        logger.info(f"Sending websocket update to group: {websocket_group} - detections: {len(detections)}")
        async_to_sync(channel_layer.group_send)(
            websocket_group,
            {
                "type": "analysis_update",
                "analysis": analysis.to_dict()
            }
        )
        
        # Log successful detection
        if logo_detections:
            logger.info(f"Logo detections found: {[d.get('label', 'Unknown') for d in logo_detections]}")
        
        return {
            'status': 'success',
            'segment_path': segment_path,
            'stream_key': stream_key,
            'detections': len(logo_detections),
            'analysis_id': str(analysis.id),
            'brands': [d['label'] for d in detections] if detections else []
        }
        
    except Exception as e:
        logger.error(f"Error processing segment event: {e}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries
            logger.info(f"Retrying in {countdown} seconds (attempt {self.request.retries + 1})")
            raise self.retry(countdown=countdown)
        
        return {'status': 'error', 'error': str(e)}

@shared_task
def start_event_processor():
    """
    Background task that continuously processes segment events.
    This replaces the file-watcher process.
    """
    consumer = SegmentEventConsumer()
    processed_count = 0
    
    try:
        # Process events in batches
        while processed_count < 50:  # Process up to 50 events per task
            event = consumer.consume_segment_event(timeout=2)
            
            if not event:
                break  # No more events
            
            # Trigger individual processing task
            process_segment_from_event.delay()
            processed_count += 1
            
        return {
            'status': 'completed',
            'processed_count': processed_count,
            'queue_length': consumer.redis_client.llen(consumer.event_key)
        }
        
    except Exception as e:
        logger.error(f"Error in event processor: {e}")
        return {'status': 'error', 'error': str(e), 'processed_count': processed_count}