#!/usr/bin/env python
"""Setup AI providers for development"""

import os
import django
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'media_analyzer.settings.development')
django.setup()

from ai_processing.models import AnalysisProvider

# Ensure CLIP is active
clip = AnalysisProvider.objects.get(provider_type='local_clip')
clip.active = True
clip.save()

# Ensure GCP is inactive
gcp = AnalysisProvider.objects.get(provider_type='gcp_vision')
gcp.active = False  
gcp.save()

print(f"✅ CLIP active: {clip.active}")
print(f"❌ GCP active: {gcp.active}")
print("🚀 Ready for logo detection!")