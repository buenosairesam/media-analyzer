#!/usr/bin/env python
"""Quick test script to verify AI pipeline works"""

import os
import django
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'media_analyzer.settings.development')
django.setup()

from ai_processing.processors.video_analyzer import VideoAnalyzer
from ai_processing.models import AnalysisProvider
from PIL import Image
import numpy as np

def test_ai_pipeline():
    print("🧪 Testing AI Pipeline...")
    
    # Check providers
    providers = AnalysisProvider.objects.all()
    print(f"📊 Found {providers.count()} providers:")
    for p in providers:
        print(f"  - {p.name} ({p.provider_type}) - Active: {p.active}")
    
    # Create test analyzer
    analyzer = VideoAnalyzer()
    
    # Create a test image (simple colored rectangle)
    print("\n🖼️  Creating test image...")
    test_image = Image.new('RGB', (640, 480), color='red')
    
    # Test synchronous analysis
    print("🔍 Running synchronous analysis...")
    try:
        result = analyzer.analyze_frame_sync(test_image)
        print(f"✅ Analysis result: {result}")
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Found {len(result.get('logos', []))} logo detections")
            for logo in result.get('logos', []):
                print(f"   - {logo['label']}: {logo['confidence']:.3f}")
    
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_pipeline()