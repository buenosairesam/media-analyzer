import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';
import { StreamStateService, StreamState, StreamSession } from '../../services/stream-state.service';
import { Stream } from '../../models/stream';
import { ExecutionManagerComponent } from '../execution-manager/execution-manager.component';
import { AnalysisManagerComponent } from '../analysis-manager/analysis-manager.component';

@Component({
  selector: 'app-unified-stream-control',
  standalone: true,
  imports: [CommonModule, FormsModule, ExecutionManagerComponent, AnalysisManagerComponent],
  template: `
    <div class="stream-control-panel">
      <div class="panel-header">
        <h3>Control Panel</h3>
        <div class="status-indicator" [class]="getStatusClass()">
          {{ getStatusText() }}
        </div>
      </div>

      <!-- Error Display -->
      <div class="error-message" *ngIf="streamState.error">
        {{ streamState.error }}
        <button (click)="clearError()" class="clear-error">✕</button>
      </div>

      <!-- Main Controls - Always Visible -->
      <div class="main-controls">
        
        <!-- Source Selection -->
        <div class="source-selection">
          <label class="source-option">
            <input 
              type="radio" 
              name="sourceType" 
              value="webcam"
              [(ngModel)]="selectedSourceType"
              [disabled]="streamState.isLoading || isStreaming">
            <span>Webcam</span>
          </label>
          <label class="source-option">
            <input 
              type="radio" 
              name="sourceType" 
              value="rtmp"
              [(ngModel)]="selectedSourceType"
              [disabled]="streamState.isLoading || isStreaming">
            <span>RTMP Stream</span>
          </label>
        </div>

        <!-- Auto-select first available RTMP stream when RTMP is selected -->
        <div class="rtmp-info" *ngIf="selectedSourceType === 'rtmp' && rtmpStreams.length > 0">
          <span class="stream-info">Stream: {{ rtmpStreams[0].stream_key }}</span>
        </div>
        <div class="rtmp-info" *ngIf="selectedSourceType === 'rtmp' && rtmpStreams.length === 0">
          <span class="no-streams">No RTMP streams available</span>
        </div>

        <!-- Start/Stop Button -->
        <div class="action-buttons">
          <button 
            *ngIf="!isStreaming"
            class="start-button" 
            (click)="startSelectedSource()" 
            [disabled]="streamState.isLoading || !canStart()">
            {{ streamState.isLoading ? 'Starting...' : 'Start Stream' }}
          </button>
          
          <button 
            *ngIf="isStreaming"
            class="stop-button" 
            (click)="stopStream()" 
            [disabled]="streamState.isLoading">
            {{ streamState.isLoading ? 'Stopping...' : 'Stop Stream' }}
          </button>
        </div>
      </div>

      <!-- Current Session Info -->
      <div class="current-session" *ngIf="streamState.currentSession">
        <h4>Active Stream</h4>
        <div class="session-info">
          <div class="session-detail">
            <span class="label">Type:</span>
            <span class="value">{{ streamState.currentSession.sourceType.toUpperCase() }}</span>
          </div>
          <div class="session-detail">
            <span class="label">Key:</span>
            <span class="value">{{ streamState.currentSession.streamKey }}</span>
          </div>
          <div class="session-detail">
            <span class="label">Started:</span>
            <span class="value">{{ formatTime(streamState.currentSession.startedAt) }}</span>
          </div>
          <div class="session-detail">
            <span class="label">Session ID:</span>
            <span class="value">{{ streamState.currentSession.id }}</span>
          </div>
        </div>
      </div>

      <!-- Stream Manager (collapsible section) -->
      <div class="source-management">
        <div class="section-header" (click)="toggleSourceManagement()">
          <h4>Stream Manager</h4>
          <span class="toggle-icon">{{ showSourceManagement ? '−' : '+' }}</span>
        </div>
        
        <div class="management-content" *ngIf="showSourceManagement">

          <!-- Available Sources -->
          <div class="available-sources" *ngIf="allStreams.length > 0">
            <h5>Available Sources</h5>
            <div class="source-list">
              <div 
                class="source-item" 
                *ngFor="let stream of allStreams"
                [class.active]="stream.status === 'active'">
                <div class="source-header">
                  <div class="source-type-badge" [class]="stream.source_type">
                    {{ stream.source_type.toUpperCase() }}
                  </div>
                  <div class="source-actions">
                    <button 
                      class="delete-button"
                      (click)="deleteStream(stream)"
                      [disabled]="streamState.isLoading || stream.status === 'active'"
                      title="Delete source">
                      🗑️
                    </button>
                  </div>
                </div>
                <div class="source-info">
                  <div class="info-row">
                    <span class="label">Stream Key:</span>
                    <span class="value mono">{{ stream.stream_key }}</span>
                  </div>
                  <div class="info-row">
                    <span class="label">Status:</span>
                    <span class="status-badge" [class]="stream.status">{{ stream.status }}</span>
                  </div>
                  <div class="info-row" *ngIf="stream.hls_playlist_url">
                    <span class="label">HLS URL:</span>
                    <span class="value mono small">{{ stream.hls_playlist_url }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="no-sources" *ngIf="allStreams.length === 0">
            <p>No sources available.</p>
          </div>
        </div>
      </div>

      <!-- Execution Manager -->
      <app-execution-manager></app-execution-manager>

      <!-- Analysis Manager -->
      <app-analysis-manager></app-analysis-manager>

      <!-- Loading Overlay -->
      <div class="loading-overlay" *ngIf="streamState.isLoading">
        <div class="spinner"></div>
      </div>
    </div>
  `,
  styles: [`
    .stream-control-panel {
      background: #f8f9fa;
      border: 1px solid #dee2e6;
      border-radius: 8px;
      padding: 20px;
      position: relative;
      min-height: 200px;
    }

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }

    .panel-header h3 {
      margin: 0;
      color: #343a40;
    }

    .status-indicator {
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .status-indicator.streaming {
      background: #d4edda;
      color: #155724;
    }

    .status-indicator.idle {
      background: #f8d7da;
      color: #721c24;
    }

    .status-indicator.loading {
      background: #fff3cd;
      color: #856404;
    }

    .error-message {
      background: #f8d7da;
      color: #721c24;
      padding: 10px;
      border-radius: 4px;
      margin-bottom: 15px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .clear-error {
      background: none;
      border: none;
      color: #721c24;
      cursor: pointer;
      font-size: 16px;
    }

    /* Main Controls Section */
    .main-controls {
      background: white;
      border: 1px solid #dee2e6;
      border-radius: 6px;
      padding: 20px;
      margin-bottom: 20px;
    }

    .source-selection {
      display: flex;
      gap: 20px;
      margin-bottom: 15px;
    }

    .source-option {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      font-weight: 500;
    }

    .source-option input[type="radio"] {
      margin: 0;
    }

    .rtmp-info {
      margin-bottom: 15px;
      padding: 8px 12px;
      border-radius: 4px;
      font-size: 14px;
    }

    .rtmp-info .stream-info {
      color: #155724;
      background: #d4edda;
      padding: 4px 8px;
      border-radius: 3px;
      font-family: monospace;
    }

    .rtmp-info .no-streams {
      color: #721c24;
      font-style: italic;
    }

    .action-buttons {
      display: flex;
      justify-content: center;
    }

    .start-button, .stop-button {
      padding: 12px 32px;
      border: none;
      border-radius: 6px;
      font-weight: 600;
      font-size: 16px;
      cursor: pointer;
      transition: all 0.2s;
      min-width: 140px;
    }

    .start-button {
      background: #28a745;
      color: white;
    }

    .start-button:hover:not(:disabled) {
      background: #1e7e34;
      transform: translateY(-1px);
    }

    .stop-button {
      background: #dc3545;
      color: white;
    }

    .stop-button:hover:not(:disabled) {
      background: #c82333;
      transform: translateY(-1px);
    }

    button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none !important;
    }

    /* Current Session Display */
    .current-session {
      background: #d4edda;
      border: 1px solid #c3e6cb;
      border-radius: 6px;
      padding: 15px;
      margin-bottom: 20px;
    }

    .current-session h4 {
      margin: 0 0 10px 0;
      color: #155724;
    }

    .session-info {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 10px;
    }

    .session-detail {
      display: flex;
      flex-direction: column;
    }

    .session-detail .label {
      font-weight: 600;
      font-size: 12px;
      color: #155724;
      text-transform: uppercase;
      margin-bottom: 2px;
    }

    .session-detail .value {
      color: #155724;
      font-family: monospace;
      font-size: 14px;
    }

    /* Source Management Section */
    .source-management {
      border: 1px solid #dee2e6;
      border-radius: 6px;
      overflow: hidden;
    }

    .section-header {
      background: #e9ecef;
      padding: 12px 15px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      user-select: none;
    }

    .section-header:hover {
      background: #dee2e6;
    }

    .section-header h4 {
      margin: 0;
      color: #495057;
      font-size: 14px;
    }

    .toggle-icon {
      font-weight: bold;
      color: #6c757d;
    }

    .management-content {
      padding: 15px;
      background: white;
    }


    /* Source List Styles */
    .source-list {
      margin-top: 15px;
    }

    .source-item {
      border: 1px solid #dee2e6;
      border-radius: 6px;
      margin-bottom: 15px;
      overflow: hidden;
    }

    .source-item.active {
      border-color: #28a745;
      background: #f8fff9;
    }

    .source-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 15px;
      background: #f8f9fa;
      border-bottom: 1px solid #dee2e6;
    }

    .source-type-badge {
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .source-type-badge.webcam {
      background: #007bff;
      color: white;
    }

    .source-type-badge.rtmp {
      background: #6f42c1;
      color: white;
    }

    .delete-button {
      background: #dc3545;
      color: white;
      border: none;
      border-radius: 4px;
      padding: 6px 10px;
      cursor: pointer;
      font-size: 16px;
      transition: background-color 0.2s;
    }

    .delete-button:hover:not(:disabled) {
      background: #c82333;
    }

    .delete-button:disabled {
      background: #6c757d;
      cursor: not-allowed;
    }

    .source-info {
      padding: 15px;
    }

    .info-row {
      display: flex;
      margin-bottom: 8px;
      align-items: flex-start;
    }

    .info-row:last-child {
      margin-bottom: 0;
    }

    .info-row .label {
      font-weight: 600;
      color: #495057;
      width: 100px;
      flex-shrink: 0;
      font-size: 12px;
      text-transform: uppercase;
    }

    .info-row .value {
      color: #212529;
      flex: 1;
      word-break: break-all;
    }

    .info-row .value.mono {
      font-family: 'Courier New', monospace;
      background: #f8f9fa;
      padding: 2px 6px;
      border-radius: 3px;
      font-size: 11px;
    }

    .info-row .value.small {
      font-size: 11px;
    }

    .status-badge {
      padding: 3px 8px;
      border-radius: 12px;
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .status-badge.active {
      background: #d4edda;
      color: #155724;
    }

    .status-badge.inactive {
      background: #f8d7da;
      color: #721c24;
    }

    .no-sources {
      text-align: center;
      padding: 40px 20px;
      color: #6c757d;
      font-style: italic;
    }

    .no-sources p {
      margin: 0;
    }

    .available-sources h5 {
      margin: 0 0 15px 0;
      color: #495057;
      font-size: 14px;
      font-weight: 600;
    }

    /* Loading Overlay */
    .loading-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(255, 255, 255, 0.9);
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      z-index: 10;
    }

    .spinner {
      width: 40px;
      height: 40px;
      border: 4px solid #f3f3f3;
      border-top: 4px solid #007bff;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `]
})
export class UnifiedStreamControlComponent implements OnInit, OnDestroy {
  streamState: StreamState = {
    isLoading: false,
    currentSession: null,
    availableStreams: [],
    error: null
  };

  selectedSourceType: 'webcam' | 'rtmp' = 'webcam';
  showSourceManagement = false;
  
  private destroy$ = new Subject<void>();

  constructor(private streamStateService: StreamStateService) {}

  ngOnInit() {
    this.streamStateService.state$
      .pipe(takeUntil(this.destroy$))
      .subscribe(state => {
        this.streamState = state;
        
        // Update source selection based on active stream
        if (state.currentSession) {
          this.selectedSourceType = state.currentSession.sourceType as 'webcam' | 'rtmp';
        }
      });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  async startSelectedSource() {
    if (this.selectedSourceType === 'webcam') {
      await this.streamStateService.startWebcamStream();
    } else if (this.selectedSourceType === 'rtmp' && this.rtmpStreams.length > 0) {
      await this.streamStateService.startRtmpStream(this.rtmpStreams[0].stream_key);
    }
  }

  async stopStream() {
    await this.streamStateService.stopCurrentStream();
  }


  toggleSourceManagement() {
    this.showSourceManagement = !this.showSourceManagement;
  }

  async deleteStream(stream: Stream) {
    if (stream.status === 'active') {
      alert('Cannot delete an active stream. Stop it first.');
      return;
    }

    if (!confirm(`Are you sure you want to delete "${stream.name}"?`)) {
      return;
    }

    try {
      // Call the backend API to delete the stream
      await this.streamStateService.deleteStream(stream.id);
    } catch (error) {
      console.error('Failed to delete stream:', error);
      alert('Failed to delete stream. Please try again.');
    }
  }

  canStart(): boolean {
    if (this.selectedSourceType === 'webcam') {
      return true;
    }
    return this.selectedSourceType === 'rtmp' && this.rtmpStreams.length > 0;
  }

  clearError() {
    // Update state to clear error
    const currentState = this.streamState;
    this.streamState = { ...currentState, error: null };
  }

  get rtmpStreams(): Stream[] {
    return this.streamState.availableStreams.filter(stream => stream.source_type === 'rtmp');
  }

  get allStreams(): Stream[] {
    return this.streamState.availableStreams;
  }

  get isStreaming(): boolean {
    return !!this.streamState.currentSession;
  }

  getStatusText(): string {
    if (this.streamState.isLoading) return 'Loading';
    if (this.streamState.currentSession) return 'Streaming';
    return 'Idle';
  }

  getStatusClass(): string {
    if (this.streamState.isLoading) return 'loading';
    if (this.streamState.currentSession) return 'streaming';
    return 'idle';
  }

  formatTime(date: Date): string {
    return new Date(date).toLocaleTimeString();
  }
}