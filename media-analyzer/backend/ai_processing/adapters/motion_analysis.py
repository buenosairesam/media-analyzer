import logging
from .base import VideoAnalysisAdapter, AdapterFactory
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class OpenCVMotionAnalysisAdapter(VideoAnalysisAdapter):
    """Local OpenCV-based motion analysis"""
    
    def analyze(self, video_path, **kwargs):
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {}
            
            # Initialize background subtractor
            backSub = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
            
            frame_count = 0
            motion_scores = []
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Apply background subtraction
                fgMask = backSub.apply(frame)
                
                # Calculate motion score (percentage of changed pixels)
                motion_pixels = cv2.countNonZero(fgMask)
                total_pixels = fgMask.shape[0] * fgMask.shape[1]
                motion_score = motion_pixels / total_pixels
                motion_scores.append(motion_score)
                
                frame_count += 1
            
            cap.release()
            
            if motion_scores:
                return {
                    'average_motion': float(np.mean(motion_scores)),
                    'max_motion': float(np.max(motion_scores)),
                    'activity_score': float(np.mean(motion_scores) * 10),  # Scale to 0-10
                    'frame_count': frame_count
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Motion analysis error: {e}")
            return {}


class GCPVideoIntelligenceAdapter(VideoAnalysisAdapter):
    """Google Cloud Video Intelligence API adapter"""
    
    def __init__(self):
        from google.cloud import videointelligence
        self.client = videointelligence.VideoIntelligenceServiceClient()
    
    def analyze(self, video_path, **kwargs):
        try:
            # Read video file
            with open(video_path, 'rb') as video_file:
                input_content = video_file.read()
            
            # Configure analysis features
            from google.cloud import videointelligence
            features = [
                videointelligence.Feature.SHOT_CHANGE_DETECTION,
                videointelligence.Feature.OBJECT_TRACKING
            ]
            
            # Start analysis
            operation = self.client.annotate_video(
                request={
                    "features": features,
                    "input_content": input_content,
                }
            )
            
            # Wait for completion (this might take a while)
            result = operation.result(timeout=300)
            
            # Process results
            analysis_results = {}
            
            # Shot changes (scene transitions)
            if result.annotation_results[0].shot_annotations:
                shots = []
                for shot in result.annotation_results[0].shot_annotations:
                    shots.append({
                        'start_time': shot.start_time_offset.total_seconds(),
                        'end_time': shot.end_time_offset.total_seconds()
                    })
                analysis_results['shots'] = shots
            
            # Object tracking
            if result.annotation_results[0].object_annotations:
                objects = []
                for obj in result.annotation_results[0].object_annotations:
                    objects.append({
                        'entity': obj.entity.description,
                        'confidence': obj.confidence,
                        'frames': len(obj.frames)
                    })
                analysis_results['tracked_objects'] = objects
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"GCP video intelligence error: {e}")
            return {}


class MotionAnalysisAdapterFactory(AdapterFactory):
    """Factory for motion analysis adapters"""
    
    @staticmethod
    def create(provider_config):
        provider_type = provider_config.get('provider_type')
        
        if provider_type == 'local_opencv':
            return OpenCVMotionAnalysisAdapter()
        elif provider_type == 'gcp_video_intelligence':
            return GCPVideoIntelligenceAdapter()
        else:
            raise ValueError(f"Unknown motion analysis provider: {provider_type}")