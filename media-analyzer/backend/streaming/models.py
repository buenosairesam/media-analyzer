from django.db import models
from django.contrib.auth.models import User


class SourceType(models.TextChoices):
    RTMP = 'rtmp', 'RTMP Stream'
    FILE = 'file', 'File Upload'
    URL = 'url', 'External URL'
    WEBCAM = 'webcam', 'Local Webcam'


class ProcessingMode(models.TextChoices):
    LIVE = 'live', 'Live Processing'
    BATCH = 'batch', 'Batch Processing'


class StreamStatus(models.TextChoices):
    INACTIVE = 'inactive', 'Inactive'
    STARTING = 'starting', 'Starting'
    ACTIVE = 'active', 'Active'
    STOPPING = 'stopping', 'Stopping'
    ERROR = 'error', 'Error'


class VideoStream(models.Model):
    name = models.CharField(max_length=200)
    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.RTMP)
    source_url = models.URLField(blank=True, null=True)  # For RTMP/URL sources
    source_file = models.FileField(upload_to='uploads/', blank=True, null=True)  # For file uploads
    processing_mode = models.CharField(max_length=20, choices=ProcessingMode.choices, default=ProcessingMode.LIVE)
    status = models.CharField(max_length=20, choices=StreamStatus.choices, default=StreamStatus.INACTIVE)
    stream_key = models.CharField(max_length=64, unique=True)  # For RTMP authentication
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class MediaSegment(models.Model):
    stream = models.ForeignKey(VideoStream, on_delete=models.CASCADE, related_name='segments')
    sequence_number = models.PositiveIntegerField()
    file_path = models.CharField(max_length=500)  # Path to .ts file
    duration = models.FloatField()  # Segment duration in seconds
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)  # AI processing status
    
    class Meta:
        ordering = ['stream', 'sequence_number']
        unique_together = ['stream', 'sequence_number']
    
    def __str__(self):
        return f"{self.stream.name} - Segment {self.sequence_number}"
