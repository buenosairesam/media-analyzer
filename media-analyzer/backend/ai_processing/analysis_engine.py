import cv2
import numpy as np
import os
from PIL import Image
import logging
from .adapters.object_detection import ObjectDetectionAdapterFactory
from .adapters.logo_detection import LogoDetectionAdapterFactory
from .adapters.text_detection import TextDetectionAdapterFactory
from .adapters.motion_analysis import MotionAnalysisAdapterFactory
from .execution_strategies.base import ExecutionStrategyFactory

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """Main analysis engine that orchestrates capability-specific adapters with execution strategies"""
    
    _strategy_logged = False
    
    def __init__(self):
        self.object_detector = None
        self.logo_detector = None
        self.text_detector = None
        self.motion_analyzer = None
        self.execution_strategy = None
        self._configure_execution_strategy()
        
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
    
    def _configure_execution_strategy(self):
        """Configure execution strategy from environment"""
        strategy_type = os.getenv('AI_PROCESSING_MODE', 'local')
        
        strategy_configs = {
            'local': lambda: ExecutionStrategyFactory.create('local'),
            'remote_lan': lambda: ExecutionStrategyFactory.create(
                'remote_lan',
                worker_host=os.getenv('AI_WORKER_HOST'),
                timeout=int(os.getenv('AI_WORKER_TIMEOUT', '30'))
            ),
            'cloud': lambda: ExecutionStrategyFactory.create('cloud')
        }
        
        try:
            if strategy_type in strategy_configs:
                self.execution_strategy = strategy_configs[strategy_type]()
            else:
                logger.warning(f"Unknown strategy type {strategy_type}, falling back to local")
                self.execution_strategy = strategy_configs['local']()
                
            if not AnalysisEngine._strategy_logged:
                logger.info(f"Configured execution strategy: {strategy_type}")
                AnalysisEngine._strategy_logged = True
            
        except Exception as e:
            logger.error(f"Failed to configure execution strategy: {e}")
            # Fallback to local
            self.execution_strategy = strategy_configs['local']()
    
    def extract_frame_from_segment(self, segment_path, timestamp=None):
        """Extract frame from video segment"""
        try:
            import os
            logger.debug(f"Attempting to extract frame from: {segment_path}")
            
            if not os.path.exists(segment_path):
                logger.error(f"Segment file does not exist: {segment_path}")
                return None
            
            cap = cv2.VideoCapture(segment_path)
            
            if not cap.isOpened():
                logger.error(f"OpenCV failed to open: {segment_path}")
                return None
                
            # For TS segments, seeking is problematic, just read first frame
            # This is suitable for real-time analysis where any frame is representative
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return Image.fromarray(frame_rgb)
            else:
                logger.error(f"Failed to read frame from {segment_path}")
            return None
                
        except Exception as e:
            logger.error(f"Error extracting frame: {e}")
            return None
    
    def analyze_frame(self, image, requested_analysis, confidence_threshold=0.5):
        """Analyze a single frame using configured adapters and execution strategy"""
        results = {}
        
        # Adapter execution map
        adapter_map = {
            'object_detection': self.object_detector,
            'logo_detection': self.logo_detector,
            'text_detection': self.text_detector
        }
        
        # Execute detection using strategy
        for analysis_type in requested_analysis:
            if analysis_type in adapter_map and adapter_map[analysis_type]:
                detections = self.execution_strategy.execute_detection(
                    adapter_map[analysis_type], 
                    image, 
                    confidence_threshold
                )
                
                # Map to expected result format
                result_key = {
                    'object_detection': 'objects',
                    'logo_detection': 'logos', 
                    'text_detection': 'text'
                }.get(analysis_type, analysis_type)
                
                results[result_key] = detections
        
        # Visual properties (always computed locally)
        if 'visual_analysis' in requested_analysis:
            results['visual'] = self._analyze_visual_properties(image)
            
        return results
    
    def health_check(self):
        """Check health of execution strategy and configured adapters"""
        try:
            strategy_info = self.execution_strategy.get_info()
            
            adapter_check = {
                'object_detection': self.object_detector,
                'logo_detection': self.logo_detector,
                'text_detection': self.text_detector,
                'motion_analysis': self.motion_analyzer
            }
            
            configured_adapters = [name for name, adapter in adapter_check.items() if adapter]
            
            return {
                'execution_strategy': strategy_info,
                'adapters_configured': configured_adapters,
                'strategy_available': self.execution_strategy.is_available()
            }
        except Exception as e:
            return {
                'error': str(e),
                'execution_strategy': None,
                'adapters_configured': [],
                'strategy_available': False
            }
    
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