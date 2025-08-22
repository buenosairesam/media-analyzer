import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, takeUntil } from 'rxjs';
import { StreamStateService, StreamState, StreamSession } from '../../services/stream-state.service';
import { Stream } from '../../models/stream';

@Component({
  selector: 'app-unified-stream-control',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="stream-control-panel">
      <div class="panel-header">
        <h3>Stream Control</h3>
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

        <!-- RTMP Stream Selection (only when RTMP is selected) -->
        <div class="rtmp-selection" *ngIf="selectedSourceType === 'rtmp'">
          <select 
            [(ngModel)]="selectedRtmpStreamKey" 
            class="rtmp-select"
            [disabled]="streamState.isLoading || isStreaming">
            <option value="">Select RTMP Stream</option>
            <option *ngFor="let stream of rtmpStreams" [value]="stream.stream_key">
              {{ stream.name }} ({{ stream.stream_key }})
            </option>
          </select>
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
        </div>
      </div>

      <!-- RTMP Management (collapsible section) -->
      <div class="rtmp-management">
        <div class="section-header" (click)="toggleRtmpManagement()">
          <h4>RTMP Management</h4>
          <span class="toggle-icon">{{ showRtmpManagement ? '−' : '+' }}</span>
        </div>
        
        <div class="management-content" *ngIf="showRtmpManagement">
          <!-- Create New RTMP Stream -->
          <div class="create-stream">
            <input 
              type="text" 
              [(ngModel)]="newStreamName" 
              placeholder="Enter stream name"
              class="stream-name-input"
              [disabled]="streamState.isLoading">
            <button 
              class="create-button" 
              (click)="createRtmpStream()" 
              [disabled]="!newStreamName || streamState.isLoading">
              Create
            </button>
          </div>

          <!-- Available RTMP Streams -->
          <div class="available-streams" *ngIf="rtmpStreams.length > 0">
            <div class="stream-list">
              <div 
                class="stream-item" 
                *ngFor="let stream of rtmpStreams">
                <div class="stream-info">
                  <div class="stream-name">{{ stream.name }}</div>
                  <div class="stream-key">{{ stream.stream_key }}</div>
                  <div class="stream-status" [class]="stream.status">{{ stream.status }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

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

    .rtmp-selection {
      margin-bottom: 15px;
    }

    .rtmp-select {
      width: 100%;
      padding: 8px 12px;
      border: 1px solid #ced4da;
      border-radius: 4px;
      font-size: 14px;
      background: white;
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

    /* RTMP Management Section */
    .rtmp-management {
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

    .create-stream {
      display: flex;
      gap: 10px;
      margin-bottom: 15px;
    }

    .stream-name-input {
      flex: 1;
      padding: 8px 12px;
      border: 1px solid #ced4da;
      border-radius: 4px;
      font-size: 14px;
    }

    .create-button {
      padding: 8px 16px;
      border: none;
      border-radius: 4px;
      font-weight: 500;
      cursor: pointer;
      background: #6c757d;
      color: white;
      transition: background-color 0.2s;
    }

    .create-button:hover:not(:disabled) {
      background: #545b62;
    }

    .stream-list {
      margin-top: 10px;
    }

    .stream-item {
      padding: 10px;
      border: 1px solid #dee2e6;
      border-radius: 4px;
      margin-bottom: 8px;
    }

    .stream-info .stream-name {
      font-weight: 600;
      color: #343a40;
      margin-bottom: 4px;
    }

    .stream-info .stream-key {
      font-family: monospace;
      font-size: 12px;
      color: #6c757d;
      margin-bottom: 4px;
    }

    .stream-status {
      font-size: 11px;
      font-weight: 500;
      text-transform: uppercase;
      padding: 2px 6px;
      border-radius: 3px;
      display: inline-block;
    }

    .stream-status.active {
      background: #d4edda;
      color: #155724;
    }

    .stream-status.inactive {
      background: #f8d7da;
      color: #721c24;
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
  selectedRtmpStreamKey = '';
  newStreamName = '';
  showRtmpManagement = false;
  
  private destroy$ = new Subject<void>();

  constructor(private streamStateService: StreamStateService) {}

  ngOnInit() {
    this.streamStateService.state$
      .pipe(takeUntil(this.destroy$))
      .subscribe(state => {
        this.streamState = state;
      });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  async startSelectedSource() {
    if (this.selectedSourceType === 'webcam') {
      await this.streamStateService.startWebcamStream();
    } else if (this.selectedSourceType === 'rtmp' && this.selectedRtmpStreamKey) {
      await this.streamStateService.startRtmpStream(this.selectedRtmpStreamKey);
    }
  }

  async stopStream() {
    await this.streamStateService.stopCurrentStream();
  }

  async createRtmpStream() {
    if (!this.newStreamName.trim()) return;
    
    await this.streamStateService.createRtmpStream(this.newStreamName.trim());
    this.newStreamName = '';
  }

  toggleRtmpManagement() {
    this.showRtmpManagement = !this.showRtmpManagement;
  }

  canStart(): boolean {
    if (this.selectedSourceType === 'webcam') {
      return true;
    }
    return this.selectedSourceType === 'rtmp' && !!this.selectedRtmpStreamKey;
  }

  clearError() {
    // Update state to clear error
    const currentState = this.streamState;
    this.streamState = { ...currentState, error: null };
  }

  get rtmpStreams(): Stream[] {
    return this.streamState.availableStreams.filter(stream => stream.source_type === 'rtmp');
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