#!/usr/bin/env python
"""Test the complete pipeline: AI analysis -> WebSocket -> Frontend"""

import os
import django
import sys
import json
import asyncio
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'media_analyzer.settings.development')
django.setup()

from ai_processing.tasks import process_video_segment
from ai_processing.models import VideoAnalysis, AnalysisProvider
from PIL import Image, ImageDraw, ImageFont
import tempfile

def create_test_image_with_apple_logo():
    """Create a test image with 'Apple' text as logo simulation"""
    img = Image.new('RGB', (640, 480), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw "Apple" text in the center
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 48)
    except:
        font = ImageFont.load_default()
    
    text = "Apple iPhone"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (640 - text_width) // 2
    y = (480 - text_height) // 2
    
    draw.text((x, y), text, fill='black', font=font)
    
    return img

def test_full_pipeline():
    print("🧪 Testing Complete Pipeline...")
    
    # Create test image
    print("🖼️  Creating test image with Apple logo simulation...")
    test_image = create_test_image_with_apple_logo()
    
    # Save to temporary file as a fake video segment
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
        test_image.save(tmp_file.name)
        fake_segment_path = tmp_file.name
    
    print(f"💾 Saved test image to: {fake_segment_path}")
    
    # Test the processing task directly
    print("🚀 Triggering analysis task...")
    try:
        result = process_video_segment('test_stream', fake_segment_path)
        print(f"✅ Task result: {result}")
        
        # Check if analysis was stored
        analysis = VideoAnalysis.objects.filter(stream_id='test_stream').last()
        if analysis:
            print(f"📊 Analysis stored: {analysis.to_dict()}")
            
            detections = analysis.detections.all()
            print(f"🎯 Found {detections.count()} detections:")
            for detection in detections:
                print(f"   - {detection.label}: {detection.confidence:.3f}")
        else:
            print("❌ No analysis found in database")
            
    except Exception as e:
        print(f"❌ Task failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            os.unlink(fake_segment_path)
        except:
            pass

if __name__ == "__main__":
    test_full_pipeline()