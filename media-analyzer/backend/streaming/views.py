from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import VideoStream, StreamStatus
from .source_adapters import SourceAdapterFactory
from ai_processing.processors.video_analyzer import VideoAnalyzer
import json
import uuid
import logging
import os

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def create_stream(request):
    """Create new stream"""
    try:
        data = json.loads(request.body)
        stream = VideoStream.objects.create(
            name=data['name'],
            source_type=data.get('source_type', 'rtmp'),
            processing_mode=data.get('processing_mode', 'live'),
            stream_key=str(uuid.uuid4())
        )
        
        return JsonResponse({
            'id': stream.id,
            'name': stream.name,
            'source_type': stream.source_type,
            'processing_mode': stream.processing_mode,
            'stream_key': stream.stream_key,
            'status': stream.status,
            'hls_playlist_url': f"{settings.HLS_BASE_URL}{settings.HLS_ENDPOINT_PATH}{stream.stream_key}.m3u8" if stream.status == 'active' else None,
            'rtmp_ingest_url': f"rtmp://{request.get_host().split(':')[0]}:{settings.RTMP_PORT}/live/{stream.stream_key}",
            'created_at': stream.created_at.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def list_streams(request):
    """List all streams"""
    streams = VideoStream.objects.all()
    return JsonResponse({
        'streams': [{
            'id': s.id,
            'name': s.name,
            'source_type': s.source_type,
            'processing_mode': s.processing_mode,
            'status': s.status,
            'hls_playlist_url': f"{settings.HLS_BASE_URL}{settings.HLS_ENDPOINT_PATH}{s.stream_key}.m3u8" if s.status == 'active' else None,
            'rtmp_ingest_url': f"rtmp://{request.get_host().split(':')[0]}:{settings.RTMP_PORT}/live/{s.stream_key}",
            'created_at': s.created_at.isoformat()
        } for s in streams]
    })


@csrf_exempt
@require_http_methods(["POST"])
def start_stream(request, stream_id):
    """Start stream processing"""
    stream = get_object_or_404(VideoStream, id=stream_id)
    
    try:
        adapter = SourceAdapterFactory.create_adapter(stream)
        success = adapter.start_processing()
        
        if success:
            return JsonResponse({
                'message': 'Stream started successfully',
                'hls_playlist_url': f"{settings.HLS_BASE_URL}{settings.HLS_ENDPOINT_PATH}{stream.stream_key}.m3u8"
            })
        else:
            return JsonResponse({'error': 'Failed to start stream'}, status=500)
            
    except Exception as e:
        logger.error(f"Error starting stream {stream_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt  
@require_http_methods(["POST"])
def stop_stream(request, stream_id):
    """Stop stream processing"""
    stream = get_object_or_404(VideoStream, id=stream_id)
    
    try:
        adapter = SourceAdapterFactory.create_adapter(stream)
        success = adapter.stop_processing()
        
        if success:
            return JsonResponse({'message': 'Stream stopped successfully'})
        else:
            return JsonResponse({'error': 'Failed to stop stream'}, status=500)
            
    except Exception as e:
        logger.error(f"Error stopping stream {stream_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def serve_hls_file(request, filename):
    """Serve HLS files with proper headers"""
    # Files are stored in project media directory  
    media_dir = settings.MEDIA_ROOT
    file_path = os.path.join(media_dir, filename)
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise Http404("HLS file not found")
    
    # Trigger analysis for new .ts segments
    if filename.endswith('.ts'):
        try:
            # Extract stream ID from UUID-based filename: 43606ec7-786c-4f7d-acf3-95981f9e5ebe-415.ts
            if '-' in filename:
                # Split by dash and take first 5 parts (UUID format)
                parts = filename.split('-')
                if len(parts) >= 5:
                    stream_id = '-'.join(parts[:5])  # Reconstruct UUID
                    
                    # Queue for analysis
                    analyzer = VideoAnalyzer()
                    analyzer.queue_segment_analysis(stream_id, file_path)
                    logger.info(f"Queued segment for analysis: {filename} (stream: {stream_id})")
            
        except Exception as e:
            logger.error(f"Error queuing analysis for {filename}: {e}")
    
    # Determine content type
    if filename.endswith('.m3u8'):
        content_type = 'application/vnd.apple.mpegurl'
    elif filename.endswith('.ts'):
        content_type = 'video/mp2t'
    else:
        content_type = 'application/octet-stream'
    
    # Read and serve file
    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type=content_type)
        response['Cache-Control'] = 'no-cache'
        return response


@csrf_exempt
@require_http_methods(["POST"])
def trigger_analysis(request, stream_id):
    """Manually trigger analysis for testing"""
    try:
        data = json.loads(request.body) if request.body else {}
        segment_path = data.get('segment_path')
        
        if not segment_path:
            # Find latest segment
            media_dir = os.path.join(settings.BASE_DIR.parent.parent, 'media')
            ts_files = [f for f in os.listdir(media_dir) if f.endswith('.ts')]
            if ts_files:
                segment_path = os.path.join(media_dir, ts_files[-1])
            else:
                return JsonResponse({'error': 'No segments found'}, status=404)
        
        analyzer = VideoAnalyzer()
        success = analyzer.queue_segment_analysis(stream_id, segment_path)
        
        if success:
            return JsonResponse({'message': 'Analysis triggered', 'segment': segment_path})
        else:
            return JsonResponse({'error': 'Failed to queue analysis'}, status=500)
            
    except Exception as e:
        logger.error(f"Error triggering analysis: {e}")
        return JsonResponse({'error': str(e)}, status=500)
