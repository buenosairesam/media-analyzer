from django.db import models
import uuid


class AnalysisProvider(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    provider_type = models.CharField(max_length=50)
    model_identifier = models.CharField(max_length=200)
    capabilities = models.JSONField(default=list)
    active = models.BooleanField(default=True)
    api_config = models.JSONField(default=dict)
    
    def __str__(self):
        return self.name


class Brand(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    search_terms = models.JSONField(default=list)
    active = models.BooleanField(default=True)
    category = models.CharField(max_length=50, null=True)
    
    def __str__(self):
        return self.name


class VideoAnalysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stream_id = models.CharField(max_length=100)
    segment_path = models.CharField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True)
    processing_time = models.FloatField(null=True)
    provider = models.ForeignKey(AnalysisProvider, on_delete=models.CASCADE, null=True, blank=True)
    analysis_type = models.CharField(max_length=50)
    confidence_threshold = models.FloatField(default=0.5)
    frame_timestamp = models.FloatField()
    external_request_id = models.CharField(max_length=200, null=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'stream_id': self.stream_id,
            'timestamp': self.timestamp.isoformat(),
            'processing_time': self.processing_time,
            'analysis_type': self.analysis_type,
            'frame_timestamp': self.frame_timestamp,
            'provider': self.provider.name if self.provider else 'local',
            'detections': [d.to_dict() for d in self.detections.all()],
            'visual': self.visual.to_dict() if hasattr(self, 'visual') else None
        }
    
    class Meta:
        indexes = [
            models.Index(fields=['stream_id', 'timestamp']),
            models.Index(fields=['analysis_type']),
        ]


class DetectionResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.ForeignKey(VideoAnalysis, on_delete=models.CASCADE, related_name='detections')
    label = models.CharField(max_length=200)
    confidence = models.FloatField()
    bbox_x = models.FloatField()
    bbox_y = models.FloatField()
    bbox_width = models.FloatField()
    bbox_height = models.FloatField()
    detection_type = models.CharField(max_length=50)  # 'object', 'logo', 'text'
    metadata = models.JSONField(default=dict)  # Provider-specific data
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'label': self.label,
            'confidence': self.confidence,
            'bbox': {
                'x': self.bbox_x,
                'y': self.bbox_y,
                'width': self.bbox_width,
                'height': self.bbox_height
            },
            'detection_type': self.detection_type,
            'metadata': self.metadata
        }
    
    class Meta:
        indexes = [
            models.Index(fields=['label']),
            models.Index(fields=['confidence']),
            models.Index(fields=['detection_type']),
        ]


class VisualAnalysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.OneToOneField(VideoAnalysis, on_delete=models.CASCADE, related_name='visual')
    dominant_colors = models.JSONField(default=list)
    brightness_level = models.FloatField()
    contrast_level = models.FloatField(null=True)
    saturation_level = models.FloatField(null=True)
    activity_score = models.FloatField(null=True)
    scene_description = models.TextField(null=True)
    
    def to_dict(self):
        return {
            'dominant_colors': self.dominant_colors,
            'brightness_level': self.brightness_level,
            'contrast_level': self.contrast_level,
            'saturation_level': self.saturation_level,
            'activity_score': self.activity_score,
            'scene_description': self.scene_description
        }


class Brand(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    search_terms = models.JSONField(default=list)  # ["Apple logo", "iPhone", "MacBook"]
    active = models.BooleanField(default=True)
    category = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class ProcessingQueue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stream_id = models.CharField(max_length=100)
    segment_path = models.CharField(max_length=500)
    priority = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'), 
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='pending')
    analysis_types = models.JSONField(default=list)  # ['yolo', 'clip_brands', 'clip_scene']
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    error_message = models.TextField(null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['stream_id']),
        ]
