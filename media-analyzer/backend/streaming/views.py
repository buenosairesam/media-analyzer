from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import VideoStream, StreamStatus
from .source_adapters import SourceAdapterFactory
import json
import uuid
import logging

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
            'hls_playlist_url': f"{settings.HLS_BASE_URL}/hls/{stream.id}/playlist.m3u8" if stream.status == 'active' else None,
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
            'hls_playlist_url': f"{settings.HLS_BASE_URL}/hls/{s.id}/playlist.m3u8" if s.status == 'active' else None,
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
                'hls_playlist_url': stream.hls_playlist_url
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
