import { Component, OnInit, OnDestroy } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';
import { StreamControlComponent } from './components/stream-control/stream-control.component';
import { StreamViewerComponent } from './components/stream-viewer/stream-viewer.component';
import { AnalysisPanelComponent } from './components/analysis-panel/analysis-panel.component';
import { AnalysisService } from './services/analysis.service';
import { DetectionResult, VisualAnalysis, Analysis } from './models/analysis';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, HttpClientModule, StreamControlComponent, StreamViewerComponent, AnalysisPanelComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'Media Analyzer';
  selectedStreamUrl: string = '';
  currentStreamId: string = '';
  currentDetections: DetectionResult[] = [];
  currentVisual?: VisualAnalysis;
  recentAnalyses: Analysis[] = [];

  constructor(private analysisService: AnalysisService) {}

  ngOnInit() {
    // Subscribe to analysis updates
    this.analysisService.detections$.subscribe(detections => {
      this.currentDetections = detections;
    });
    
    this.analysisService.visual$.subscribe(visual => {
      this.currentVisual = visual || undefined;
    });
    
    this.analysisService.analyses$.subscribe(analyses => {
      this.recentAnalyses = analyses;
    });
  }

  ngOnDestroy() {
    this.analysisService.disconnect();
  }

  onStreamSelected(streamUrl: string) {
    console.log('App received stream URL:', streamUrl);
    this.selectedStreamUrl = streamUrl;
    
    // Extract stream ID from URL: /streaming/hls/43606ec7-786c-4f7d-acf3-95981f9e5ebe.m3u8
    const streamIdMatch = streamUrl.match(/hls\/([0-9a-f-]+)\.m3u8/);
    if (streamIdMatch) {
      this.currentStreamId = streamIdMatch[1];
      console.log('Extracted stream ID:', this.currentStreamId);
      // Connect to WebSocket for this stream
      this.analysisService.connectToStream(this.currentStreamId);
    } else {
      console.error('Could not extract stream ID from URL:', streamUrl);
    }
  }
}
