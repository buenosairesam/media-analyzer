import logging
from .base import DetectionAdapter, AdapterFactory
import io

logger = logging.getLogger(__name__)


class GCPObjectDetectionAdapter(DetectionAdapter):
    """Google Cloud Vision object detection"""
    
    def __init__(self):
        from google.cloud import vision
        self.client = vision.ImageAnnotatorClient()
    
    def detect(self, image, confidence_threshold=0.5):
        try:
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            image_bytes = img_byte_arr.getvalue()
            
            # GCP Vision API call
            from google.cloud import vision
            vision_image = vision.Image(content=image_bytes)
            response = self.client.object_localization(image=vision_image)
            
            results = []
            for obj in response.localized_object_annotations:
                if obj.score >= confidence_threshold:
                    # Convert normalized vertices to bbox
                    vertices = obj.bounding_poly.normalized_vertices
                    x_coords = [v.x for v in vertices]
                    y_coords = [v.y for v in vertices]
                    
                    bbox = {
                        'x': min(x_coords),
                        'y': min(y_coords),
                        'width': max(x_coords) - min(x_coords),
                        'height': max(y_coords) - min(y_coords)
                    }
                    
                    results.append({
                        'label': obj.name,
                        'confidence': obj.score,
                        'bbox': bbox
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"GCP object detection error: {e}")
            return []


class YOLOObjectDetectionAdapter(DetectionAdapter):
    """Local YOLO object detection"""
    
    def __init__(self, model_path="yolov8n.pt"):
        self.model_path = model_path
        self.model = None
        
    def _load_model(self):
        if not self.model:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
    
    def detect(self, image, confidence_threshold=0.5):
        try:
            self._load_model()
            
            # Convert PIL to OpenCV format
            import cv2
            import numpy as np
            img_array = np.array(image)
            
            # YOLO inference
            results = self.model(img_array, conf=confidence_threshold)
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get normalized coordinates
                        x1, y1, x2, y2 = box.xyxyn[0].tolist()
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        class_name = self.model.names[class_id]
                        
                        bbox = {
                            'x': x1,
                            'y': y1,
                            'width': x2 - x1,
                            'height': y2 - y1
                        }
                        
                        detections.append({
                            'label': class_name,
                            'confidence': confidence,
                            'bbox': bbox
                        })
            
            return detections
            
        except Exception as e:
            logger.error(f"YOLO object detection error: {e}")
            return []


class ObjectDetectionAdapterFactory(AdapterFactory):
    """Factory for object detection adapters"""
    
    @staticmethod
    def create(provider_config):
        provider_type = provider_config.get('provider_type')
        
        if provider_type == 'gcp_vision':
            return GCPObjectDetectionAdapter()
        elif provider_type == 'local_yolo':
            model_path = provider_config.get('model_identifier', 'yolov8n.pt')
            return YOLOObjectDetectionAdapter(model_path)
        else:
            raise ValueError(f"Unknown object detection provider: {provider_type}")