from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import VideoStream, StreamStatus
from .source_adapters import SourceAdapterFactory
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
    media_dir = os.path.join(settings.BASE_DIR.parent.parent, 'media')
    file_path = os.path.join(media_dir, filename)
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise Http404("HLS file not found")
    
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
