#!/usr/bin/env python
"""Test frontend integration by creating sample analysis data"""

import os
import django
import sys
from pathlib import Path

# Configure Django
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'media_analyzer.settings.development')
django.setup()

from ai_processing.models import VideoAnalysis, DetectionResult, VisualAnalysis, AnalysisProvider
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def create_sample_analysis():
    """Create sample analysis data for testing frontend"""
    print("🎯 Creating sample analysis data...")
    
    # Get CLIP provider
    provider = AnalysisProvider.objects.filter(provider_type='local_clip').first()
    
    # Create analysis
    analysis = VideoAnalysis.objects.create(
        stream_id='test_stream',
        segment_path='/fake/path.ts',
        provider=provider,
        analysis_type='logo_detection',
        frame_timestamp=0.0,
        confidence_threshold=0.3
    )
    
    # Create sample detections
    DetectionResult.objects.create(
        analysis=analysis,
        label='Apple',
        confidence=0.85,
        bbox_x=0.2,
        bbox_y=0.3,
        bbox_width=0.3,
        bbox_height=0.2,
        detection_type='logo'
    )
    
    DetectionResult.objects.create(
        analysis=analysis,
        label='Google',
        confidence=0.72,
        bbox_x=0.5,
        bbox_y=0.1,
        bbox_width=0.25,
        bbox_height=0.15,
        detection_type='logo'
    )
    
    # Create visual analysis
    VisualAnalysis.objects.create(
        analysis=analysis,
        dominant_colors=[[255, 0, 0], [0, 255, 0], [0, 0, 255]],
        brightness_level=0.7,
        contrast_level=0.5,
        saturation_level=0.8
    )
    
    print(f"✅ Created analysis: {analysis.to_dict()}")
    
    # Try to send via WebSocket
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                "stream_test_stream",
                {
                    "type": "analysis_update",
                    "analysis": analysis.to_dict()
                }
            )
            print("📡 Sent WebSocket update")
        else:
            print("⚠️  No channel layer configured")
    except Exception as e:
        print(f"❌ WebSocket send failed: {e}")

if __name__ == "__main__":
    create_sample_analysis()