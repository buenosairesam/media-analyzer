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
  private currentSessionId: string | null = null;
  private connectedStreamKey: string | null = null;
  
  public detections$ = this.currentDetections.asObservable();
  public visual$ = this.currentVisual.asObservable();
  public analyses$ = this.recentAnalyses.asObservable();

  constructor(private websocketService: WebsocketService) {
    // Subscribe to WebSocket analysis updates
    this.websocketService.analysis$.subscribe(analysis => {
      this.handleAnalysisUpdate(analysis);
    });
  }

  connectToStream(streamKey: string, sessionId?: string) {
    // Set current session for filtering
    this.currentSessionId = sessionId || `session_${Date.now()}`;
    this.connectedStreamKey = streamKey;
    
    // Clear existing analysis data when starting new session
    this.clearAnalysis();
    
    // Connect to WebSocket with session ID
    this.websocketService.subscribe(streamKey, this.currentSessionId);
    
    console.log('Connected to stream analysis:', {
      streamKey,
      sessionId: this.currentSessionId
    });
  }

  disconnect() {
    this.websocketService.unsubscribe();
    this.websocketService.disconnect();
    this.clearAnalysis();
    this.currentSessionId = null;
    this.connectedStreamKey = null;
  }

  private handleAnalysisUpdate(analysis: Analysis) {
    // Only process analysis if we have an active session
    if (!this.currentSessionId) {
      console.log('Ignoring analysis - no active session');
      return;
    }
    
    console.log('Processing analysis update for session:', this.currentSessionId, analysis);
    
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
    
    console.log('Analysis update processed:', {
      sessionId: this.currentSessionId,
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

  getCurrentSessionId(): string | null {
    return this.currentSessionId;
  }

  isConnectedToStream(streamKey: string): boolean {
    return this.connectedStreamKey === streamKey && !!this.currentSessionId;
  }
}
