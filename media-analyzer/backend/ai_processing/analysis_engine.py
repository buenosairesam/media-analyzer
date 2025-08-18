import cv2
import numpy as np
from PIL import Image
import logging
from .adapters.object_detection import ObjectDetectionAdapterFactory
from .adapters.logo_detection import LogoDetectionAdapterFactory
from .adapters.text_detection import TextDetectionAdapterFactory
from .adapters.motion_analysis import MotionAnalysisAdapterFactory

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """Main analysis engine that orchestrates capability-specific adapters"""
    
    def __init__(self):
        self.object_detector = None
        self.logo_detector = None
        self.text_detector = None
        self.motion_analyzer = None
        
    def configure_providers(self, provider_config):
        """Configure adapters based on provider settings"""
        if 'object_detection' in provider_config:
            self.object_detector = ObjectDetectionAdapterFactory.create(
                provider_config['object_detection']
            )
            
        if 'logo_detection' in provider_config:
            self.logo_detector = LogoDetectionAdapterFactory.create(
                provider_config['logo_detection']
            )
            
        if 'text_detection' in provider_config:
            self.text_detector = TextDetectionAdapterFactory.create(
                provider_config['text_detection']
            )
            
        if 'motion_analysis' in provider_config:
            self.motion_analyzer = MotionAnalysisAdapterFactory.create(
                provider_config['motion_analysis']
            )
    
    def extract_frame_from_segment(self, segment_path, timestamp=None):
        """Extract frame from video segment"""
        try:
            cap = cv2.VideoCapture(segment_path)
            if not cap.isOpened():
                return None
                
            # For TS segments, seeking is problematic, just read first frame
            # This is suitable for real-time analysis where any frame is representative
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return Image.fromarray(frame_rgb)
            return None
                
        except Exception as e:
            logger.error(f"Error extracting frame: {e}")
            return None
    
    def analyze_frame(self, image, requested_analysis, confidence_threshold=0.5):
        """Analyze a single frame using configured adapters"""
        results = {}
        
        # Object detection
        if 'object_detection' in requested_analysis and self.object_detector:
            results['objects'] = self.object_detector.detect(image, confidence_threshold)
            
        # Logo detection  
        if 'logo_detection' in requested_analysis and self.logo_detector:
            results['logos'] = self.logo_detector.detect(image, confidence_threshold)
            
        # Text detection
        if 'text_detection' in requested_analysis and self.text_detector:
            results['text'] = self.text_detector.detect(image, confidence_threshold)
            
        # Visual properties (always computed locally)
        if 'visual_analysis' in requested_analysis:
            results['visual'] = self._analyze_visual_properties(image)
            
        return results
    
    def analyze_video_segment(self, segment_path, requested_analysis):
        """Analyze video segment for temporal features"""
        results = {}
        
        # Motion analysis
        if 'motion_analysis' in requested_analysis and self.motion_analyzer:
            results['motion'] = self.motion_analyzer.analyze(segment_path)
            
        return results
    
    def _analyze_visual_properties(self, image):
        """Local visual property analysis"""
        img_array = np.array(image)
        
        # Dominant colors
        dominant_colors = self._get_dominant_colors(img_array)
        
        # Visual metrics
        brightness = float(np.mean(img_array)) / 255.0
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        contrast = float(np.std(gray)) / 255.0
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        saturation = float(np.mean(hsv[:,:,1])) / 255.0
        
        return {
            'dominant_colors': dominant_colors,
            'brightness_level': brightness,
            'contrast_level': contrast,
            'saturation_level': saturation
        }
    
    def _get_dominant_colors(self, image_array, k=3):
        try:
            data = image_array.reshape((-1, 3))
            data = np.float32(data)
            
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            return centers.astype(int).tolist()
        except:
            return [[128, 128, 128]]