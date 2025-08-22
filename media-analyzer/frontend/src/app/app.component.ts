import { Component, OnInit, OnDestroy, ViewChild } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';
import { StreamControlComponent } from './components/stream-control/stream-control.component';
import { StreamViewerComponent } from './components/stream-viewer/stream-viewer.component';
import { AnalysisPanelComponent } from './components/analysis-panel/analysis-panel.component';
import { AnalysisService } from './services/analysis.service';
import { StreamService } from './services/stream.service';
import { DetectionResult, VisualAnalysis, Analysis } from './models/analysis';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, HttpClientModule, StreamControlComponent, StreamViewerComponent, AnalysisPanelComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit, OnDestroy {
  @ViewChild(StreamViewerComponent) streamViewer!: StreamViewerComponent;
  
  title = 'Media Analyzer';
  selectedStreamUrl: string = '';
  currentStreamId: string = '';
  currentDetections: DetectionResult[] = [];
  currentVisual?: VisualAnalysis;
  recentAnalyses: Analysis[] = [];

  constructor(
    private analysisService: AnalysisService,
    private streamService: StreamService
  ) {}

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
    
    // Extract filename from backend URL, then construct a browser-resolvable URL
    const filename = streamUrl.split('/').pop() || '';
    this.selectedStreamUrl = `/streaming/${filename}`;
    console.log('Using HLS URL:', this.selectedStreamUrl);
    
    // Retry function to get active stream (with small delays to allow DB update)
    const getActiveStreamWithRetry = (attempt = 1, maxAttempts = 3) => {
      this.streamService.getStreams().subscribe({
        next: (response) => {
          const activeStream = response.streams.find(stream => stream.status === 'active');
          if (activeStream) {
            this.currentStreamId = activeStream.stream_key;
            console.log('Found active stream with key:', this.currentStreamId);
            // Connect to WebSocket for this stream
            this.analysisService.connectToStream(this.currentStreamId);
          } else if (attempt < maxAttempts) {
            console.log(`No active stream found (attempt ${attempt}/${maxAttempts}), retrying in 1s...`);
            setTimeout(() => getActiveStreamWithRetry(attempt + 1, maxAttempts), 1000);
          } else {
            console.log('No active stream found after retries, falling back to filename parsing');
            this.fallbackToFilenameExtraction(filename);
          }
        },
        error: (error) => {
          console.error('Failed to get streams from API:', error);
          this.fallbackToFilenameExtraction(filename);
        }
      });
    };
    
    // Start the retry process
    getActiveStreamWithRetry();
  }
  
  private fallbackToFilenameExtraction(filename: string) {
    const streamIdMatch = filename.match(/^([a-zA-Z0-9-]+)\.m3u8$/);
    if (streamIdMatch) {
      this.currentStreamId = streamIdMatch[1];
      console.log('Fallback: Extracted stream ID from filename:', this.currentStreamId);
      this.analysisService.connectToStream(this.currentStreamId);
    } else {
      console.error('Could not extract stream ID from filename:', filename);
    }
  }

  onStreamStopped() {
    console.log('Stream stopped - clearing player');
    // Clear the stream from player
    if (this.streamViewer) {
      this.streamViewer.clearStream();
    }
    // Clear app state
    this.selectedStreamUrl = '';
    this.currentStreamId = '';
    this.currentDetections = [];
    this.currentVisual = undefined;
    // Disconnect from WebSocket
    this.analysisService.disconnect();
  }
}
