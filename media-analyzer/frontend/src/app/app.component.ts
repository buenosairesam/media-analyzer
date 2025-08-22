import { Component, OnInit, OnDestroy, ViewChild } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';
import { UnifiedStreamControlComponent } from './components/unified-stream-control/unified-stream-control.component';
import { StreamViewerComponent } from './components/stream-viewer/stream-viewer.component';
import { AnalysisPanelComponent } from './components/analysis-panel/analysis-panel.component';
import { AnalysisService } from './services/analysis.service';
import { StreamStateService } from './services/stream-state.service';
import { DetectionResult, VisualAnalysis, Analysis } from './models/analysis';
import { Subject, takeUntil } from 'rxjs';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, HttpClientModule, UnifiedStreamControlComponent, StreamViewerComponent, AnalysisPanelComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit, OnDestroy {
  @ViewChild(StreamViewerComponent) streamViewer!: StreamViewerComponent;
  
  title = 'Media Analyzer';
  selectedStreamUrl: string = '';
  currentDetections: DetectionResult[] = [];
  currentVisual?: VisualAnalysis;
  recentAnalyses: Analysis[] = [];
  
  private destroy$ = new Subject<void>();

  constructor(
    private analysisService: AnalysisService,
    private streamStateService: StreamStateService
  ) {}

  ngOnInit() {
    // Subscribe to stream URL changes from centralized state
    this.streamStateService.currentStreamUrl$
      .pipe(takeUntil(this.destroy$))
      .subscribe(streamUrl => {
        this.selectedStreamUrl = streamUrl;
        
        // Clear stream viewer when URL is empty (stream stopped)
        if (!streamUrl && this.streamViewer) {
          this.streamViewer.clearStream();
        }
      });

    // Subscribe to analysis updates
    this.analysisService.detections$
      .pipe(takeUntil(this.destroy$))
      .subscribe(detections => {
        console.log('AppComponent - received detections:', detections.length, detections);
        this.currentDetections = detections;
      });
    
    this.analysisService.visual$
      .pipe(takeUntil(this.destroy$))
      .subscribe(visual => {
        this.currentVisual = visual || undefined;
      });
    
    this.analysisService.analyses$
      .pipe(takeUntil(this.destroy$))
      .subscribe(analyses => {
        this.recentAnalyses = analyses;
      });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
    this.analysisService.disconnect();
  }
}
