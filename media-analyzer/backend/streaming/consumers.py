import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from ai_processing.models import VideoAnalysis

logger = logging.getLogger(__name__)


class StreamAnalysisConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time analysis updates"""
    
    async def connect(self):
        # Initialize subscription set for dynamic stream groups
        self.subscribed_streams = set()
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
                if stream_key and stream_key not in self.subscribed_streams:
                    self.subscribed_streams.add(stream_key)
                    await self.channel_layer.group_add(f"stream_{stream_key}", self.channel_name)
                    await self.send_recent_analysis(stream_key)
            elif message_type == 'unsubscribe':
                stream_key = data.get('stream_id')  # Frontend still sends 'stream_id' but it's actually stream_key
                if stream_key and stream_key in self.subscribed_streams:
                    self.subscribed_streams.remove(stream_key)
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
    def get_recent_analysis(self, stream_key):
        """Get recent analysis results for a given stream"""
        try:
            analyses = VideoAnalysis.objects.filter(
                stream_key=stream_key
            ).order_by('-timestamp')[:5]
            return [analysis.to_dict() for analysis in analyses]
        except Exception as e:
            logger.error(f"Error getting recent analysis for {stream_key}: {e}")
            return []
    
    async def send_recent_analysis(self, stream_key):
        """Send recent analysis results to client for the given stream"""
        recent_analyses = await self.get_recent_analysis(stream_key)
        if recent_analyses:
            await self.send(text_data=json.dumps({
                'type': 'recent_analysis',
                'analyses': recent_analyses
            }))