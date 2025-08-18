import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from ai_processing.models import VideoAnalysis

logger = logging.getLogger(__name__)


class StreamAnalysisConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time analysis updates"""
    
    async def connect(self):
        self.stream_id = self.scope['url_route']['kwargs']['stream_id']
        self.room_group_name = f'stream_{self.stream_id}'
        
        # Join stream group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"WebSocket connected for stream {self.stream_id}")
        
        # Send recent analysis results
        await self.send_recent_analysis()
    
    async def disconnect(self, close_code):
        # Leave stream group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected for stream {self.stream_id}")
    
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
    def get_recent_analysis(self):
        """Get recent analysis results for stream"""
        try:
            analyses = VideoAnalysis.objects.filter(
                stream_id=self.stream_id
            ).order_by('-timestamp')[:5]
            
            return [analysis.to_dict() for analysis in analyses]
        except Exception as e:
            logger.error(f"Error getting recent analysis: {e}")
            return []
    
    async def send_recent_analysis(self):
        """Send recent analysis results to client"""
        recent_analyses = await self.get_recent_analysis()
        if recent_analyses:
            await self.send(text_data=json.dumps({
                'type': 'recent_analysis',
                'analyses': recent_analyses
            }))