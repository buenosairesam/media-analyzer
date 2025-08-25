import logging
from .base import DetectionAdapter, AdapterFactory
import io

logger = logging.getLogger(__name__)


class GCPTextDetectionAdapter(DetectionAdapter):
    """Google Cloud Vision text detection (OCR)"""
    
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
            response = self.client.text_detection(image=vision_image)
            
            results = []
            # Skip first annotation (full text), process individual words/lines
            for text in response.text_annotations[1:]:
                vertices = text.bounding_poly.vertices
                x_coords = [v.x for v in vertices]
                y_coords = [v.y for v in vertices]
                
                # Normalize using image dimensions
                width, height = image.size
                bbox = {
                    'x': min(x_coords) / width,
                    'y': min(y_coords) / height,
                    'width': (max(x_coords) - min(x_coords)) / width,
                    'height': (max(y_coords) - min(y_coords)) / height
                }
                
                results.append({
                    'label': text.description,
                    'confidence': 1.0,  # GCP doesn't provide text confidence
                    'bbox': bbox
                })
            
            return results
            
        except Exception as e:
            logger.error(f"GCP text detection error: {e}")
            return []


class TesseractTextDetectionAdapter(DetectionAdapter):
    """Local Tesseract OCR adapter"""
    
    def __init__(self):
        try:
            import pytesseract
            self.tesseract = pytesseract
        except ImportError:
            logger.error("pytesseract not installed")
            self.tesseract = None
    
    def detect(self, image, confidence_threshold=0.5):
        if not self.tesseract:
            return []
            
        try:
            import cv2
            import numpy as np
            
            # Convert to OpenCV format
            img_array = np.array(image)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Get bounding box data
            data = self.tesseract.image_to_data(gray, output_type=self.tesseract.Output.DICT)
            
            results = []
            height, width = gray.shape
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                conf = int(data['conf'][i])
                
                if text and conf > (confidence_threshold * 100):
                    # Normalize coordinates
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    
                    bbox = {
                        'x': x / width,
                        'y': y / height,
                        'width': w / width,
                        'height': h / height
                    }
                    
                    results.append({
                        'label': text,
                        'confidence': conf / 100.0,
                        'bbox': bbox
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Tesseract text detection error: {e}")
            return []


class TextDetectionAdapterFactory(AdapterFactory):
    """Factory for text detection adapters"""
    
    @staticmethod
    def create(provider_config):
        provider_type = provider_config.get('provider_type')
        
        if provider_type == 'gcp_vision':
            return GCPTextDetectionAdapter()
        elif provider_type == 'local_tesseract':
            return TesseractTextDetectionAdapter()
        else:
            raise ValueError(f"Unknown text detection provider: {provider_type}")