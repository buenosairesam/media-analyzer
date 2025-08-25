import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { WebsocketService } from './websocket.service';
import { Analysis, DetectionResult, VisualAnalysis } from '../models/analysis';

@Injectable({
  providedIn: 'root'
})
export class AnalysisService {
  private currentDetections = new BehaviorSubject<DetectionResult[]>([]);
  private currentVisual = new BehaviorSubject<VisualAnalysis | null>(null);
  private recentAnalyses = new BehaviorSubject<Analysis[]>([]);
  
  public detections$ = this.currentDetections.asObservable();
  public visual$ = this.currentVisual.asObservable();
  public analyses$ = this.recentAnalyses.asObservable();

  constructor(private websocketService: WebsocketService) {
    // Subscribe to WebSocket analysis updates
    this.websocketService.analysis$.subscribe(analysis => {
      this.handleAnalysisUpdate(analysis);
    });
  }

  connectToStream(streamId: string) {
    this.websocketService.connect(streamId);
  }

  disconnect() {
    this.websocketService.disconnect();
    this.currentDetections.next([]);
    this.currentVisual.next(null);
  }

  private handleAnalysisUpdate(analysis: Analysis) {
    // Update recent analyses list
    const current = this.recentAnalyses.value;
    const updated = [analysis, ...current.slice(0, 9)]; // Keep last 10
    this.recentAnalyses.next(updated);
    
    // Update current detections (latest analysis only)
    const detections = analysis.detections || [];
    this.currentDetections.next(detections);
    
    // Update visual analysis
    if (analysis.visual) {
      this.currentVisual.next(analysis.visual);
    }
    
    console.log('Analysis update:', {
      detections: detections.length,
      visual: !!analysis.visual,
      timestamp: analysis.timestamp
    });
  }

  getCurrentDetections(): DetectionResult[] {
    return this.currentDetections.value;
  }

  getCurrentVisual(): VisualAnalysis | null {
    return this.currentVisual.value;
  }

  getDetectionsByType(type: string): DetectionResult[] {
    return this.currentDetections.value.filter(d => d.detection_type === type);
  }

  clearAnalysis() {
    this.currentDetections.next([]);
    this.currentVisual.next(null);
    this.recentAnalyses.next([]);
  }
}
