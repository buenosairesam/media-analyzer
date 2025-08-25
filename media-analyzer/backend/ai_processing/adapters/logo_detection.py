import logging
from .base import DetectionAdapter, AdapterFactory
import io

logger = logging.getLogger(__name__)


class GCPLogoDetectionAdapter(DetectionAdapter):
    """Google Cloud Vision logo detection"""
    
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
            response = self.client.logo_detection(image=vision_image)
            
            results = []
            for logo in response.logo_annotations:
                if logo.score >= confidence_threshold:
                    # Convert pixel vertices to normalized bbox
                    vertices = logo.bounding_poly.vertices
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
                        'label': logo.description,
                        'confidence': logo.score,
                        'bbox': bbox
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"GCP logo detection error: {e}")
            return []


class CLIPLogoDetectionAdapter(DetectionAdapter):
    """Local CLIP-based logo/brand detection"""
    
    def __init__(self, model_identifier="openai/clip-vit-base-patch32"):
        self.model_identifier = model_identifier
        self.model = None
        self.processor = None
        
    def _load_model(self):
        if not self.model:
            from transformers import CLIPProcessor, CLIPModel
            self.model = CLIPModel.from_pretrained(self.model_identifier)
            self.processor = CLIPProcessor.from_pretrained(self.model_identifier)
    
    def cleanup(self):
        """Release model and processor memory"""
        if self.model:
            del self.model
            self.model = None
        if self.processor:
            del self.processor
            self.processor = None
        
        import torch
        import gc
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
    
    def detect(self, image, confidence_threshold=0.5):
        try:
            self._load_model()
            from ..models import Brand
            
            # Get active brands from database
            active_brands = Brand.objects.filter(active=True)
            if not active_brands.exists():
                return []
            
            # Collect search terms
            text_prompts = []
            brand_mapping = {}
            
            for brand in active_brands:
                for term in brand.search_terms:
                    prompt = f"a photo containing {term}"
                    text_prompts.append(prompt)
                    brand_mapping[len(text_prompts)-1] = brand.name
            
            text_prompts.append("a photo with no brands or logos")
            
            # CLIP inference
            inputs = self.processor(text=text_prompts, images=image, return_tensors="pt", padding=True)
            
            import torch
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = outputs.logits_per_image.softmax(dim=1)
                
                # Clear GPU cache immediately after inference
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                # Clear input tensors
                del inputs
                del outputs
            
            results = []
            for i, prob in enumerate(probs[0][:-1]):
                confidence = float(prob)
                if confidence > confidence_threshold and i in brand_mapping:
                    results.append({
                        'label': brand_mapping[i],
                        'confidence': confidence,
                        'bbox': {'x': 0, 'y': 0, 'width': 1, 'height': 1}  # Full frame for CLIP
                    })
            
            # Clear probability tensors
            del probs
            
            return sorted(results, key=lambda x: x['confidence'], reverse=True)[:5]
            
        except Exception as e:
            logger.error(f"CLIP logo detection error: {e}")
            return []
        finally:
            # Force garbage collection after processing
            import gc
            gc.collect()


class LogoDetectionAdapterFactory(AdapterFactory):
    """Factory for logo detection adapters"""
    
    @staticmethod
    def create(provider_config):
        provider_type = provider_config.get('provider_type')
        
        if provider_type == 'gcp_vision':
            return GCPLogoDetectionAdapter()
        elif provider_type == 'local_clip':
            model_id = provider_config.get('model_identifier', 'openai/clip-vit-base-patch32')
            return CLIPLogoDetectionAdapter(model_id)
        else:
            raise ValueError(f"Unknown logo detection provider: {provider_type}")