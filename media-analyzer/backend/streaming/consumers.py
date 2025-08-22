import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from ai_processing.models import VideoAnalysis

logger = logging.getLogger(__name__)


class StreamAnalysisConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time analysis updates"""
    
    async def connect(self):
        # Initialize subscription set for dynamic stream groups
        self.subscribed_streams = set()
        self.stream_sessions = {}  # Track session IDs per stream
        await self.accept()
        logger.info("WebSocket connected - ready to subscribe to streams")
    
    async def disconnect(self, close_code):
        # Leave all subscribed stream groups
        for stream_key in getattr(self, 'subscribed_streams', []):
            await self.channel_layer.group_discard(f"stream_{stream_key}", self.channel_name)
        logger.info("WebSocket disconnected")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            elif message_type == 'subscribe':
                stream_key = data.get('stream_id')  # Frontend still sends 'stream_id' but it's actually stream_key
                session_id = data.get('session_id')  # Get session ID from frontend
                if stream_key and stream_key not in self.subscribed_streams:
                    self.subscribed_streams.add(stream_key)
                    self.stream_sessions[stream_key] = session_id  # Track session for this stream
                    # Store session in cache for HTTP access (persistent)
                    cache.set(f"stream_session_{stream_key}", session_id, None)  # No expiration
                    await self.channel_layer.group_add(f"stream_{stream_key}", self.channel_name)
                    await self.send_recent_analysis(stream_key, session_id)
            elif message_type == 'unsubscribe':
                stream_key = data.get('stream_id')  # Frontend still sends 'stream_id' but it's actually stream_key
                if stream_key and stream_key in self.subscribed_streams:
                    self.subscribed_streams.remove(stream_key)
                    self.stream_sessions.pop(stream_key, None)  # Remove session tracking
                    await self.channel_layer.group_discard(f"stream_{stream_key}", self.channel_name)
            elif message_type == 'request_analysis':
                # Trigger analysis if needed
                pass
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
    
    async def analysis_update(self, event):
        """Handle analysis update from task"""
        await self.send(text_data=json.dumps({
            'type': 'analysis_update',
            'analysis': event['analysis']
        }))
    
    @database_sync_to_async
    def get_recent_analysis(self, stream_key, session_id=None):
        """Get recent analysis results for a given stream and session"""
        try:
            query = VideoAnalysis.objects.filter(stream_key=stream_key)
            if session_id:
                query = query.filter(session_id=session_id)
            analyses = query.order_by('-timestamp')[:5]
            return [analysis.to_dict() for analysis in analyses]
        except Exception as e:
            logger.error(f"Error getting recent analysis for {stream_key}: {e}")
            return []
    
    async def send_recent_analysis(self, stream_key, session_id=None):
        """Send recent analysis results to client for the given stream and session"""
        recent_analyses = await self.get_recent_analysis(stream_key, session_id)
        if recent_analyses:
            await self.send(text_data=json.dumps({
                'type': 'recent_analysis',
                'analyses': recent_analyses
            }))