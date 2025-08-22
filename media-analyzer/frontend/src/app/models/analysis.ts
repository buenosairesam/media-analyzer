export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface DetectionResult {
  id: string;
  label: string;
  confidence: number;
  bbox: BoundingBox;
  detection_type: 'object' | 'logo' | 'text';
  metadata?: any;
}

export interface VisualAnalysis {
  dominant_colors: number[][];
  brightness_level: number;
  contrast_level?: number;
  saturation_level?: number;
  activity_score?: number;
  scene_description?: string;
}

export interface Analysis {
  id: string;
  stream_id: string;
  session_id?: string;
  timestamp: string;
  processing_time?: number;
  analysis_type: string;
  frame_timestamp: number;
  provider: string;
  detections: DetectionResult[];
  visual?: VisualAnalysis;
}
