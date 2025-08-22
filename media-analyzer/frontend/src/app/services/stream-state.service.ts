import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, combineLatest, distinctUntilChanged, map } from 'rxjs';
import { StreamService } from './stream.service';
import { AnalysisService } from './analysis.service';
import { Stream } from '../models/stream';

export interface StreamSession {
  id: string;
  streamKey: string;
  hlsUrl: string;
  sourceType: 'webcam' | 'rtmp';
  startedAt: Date;
}

export interface StreamState {
  isLoading: boolean;
  currentSession: StreamSession | null;
  availableStreams: Stream[];
  error: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class StreamStateService {
  private readonly SESSION_KEY = 'media_analyzer_session';
  
  private state = new BehaviorSubject<StreamState>({
    isLoading: false,
    currentSession: null,
    availableStreams: [],
    error: null
  });

  public state$ = this.state.asObservable();
  
  // Derived observables for common use cases
  public isStreaming$ = this.state$.pipe(
    map(state => !!state.currentSession),
    distinctUntilChanged()
  );
  
  public currentStreamUrl$ = this.state$.pipe(
    map(state => state.currentSession?.hlsUrl || ''),
    distinctUntilChanged()
  );
  
  public isLoading$ = this.state$.pipe(
    map(state => state.isLoading),
    distinctUntilChanged()
  );

  constructor(
    private streamService: StreamService,
    private analysisService: AnalysisService
  ) {
    this.loadAvailableStreams();
    this.restoreSession();
  }

  // Stream Operations
  async startWebcamStream(): Promise<void> {
    this.updateState({ isLoading: true, error: null });
    
    try {
      // Stop any existing stream first
      await this.stopCurrentStream();
      
      const stream = await this.streamService.startWebcamStream().toPromise();
      if (!stream) throw new Error('Failed to start webcam stream');
      
      const session = this.createSession(stream.stream_key, stream.hls_playlist_url || '', 'webcam');
      await this.activateSession(session);
      
    } catch (error: any) {
      this.handleError(error);
    } finally {
      this.updateState({ isLoading: false });
    }
  }

  async startRtmpStream(streamKey: string): Promise<void> {
    this.updateState({ isLoading: true, error: null });
    
    try {
      // Stop any existing stream first
      await this.stopCurrentStream();
      
      const response = await this.streamService.startStream(streamKey).toPromise();
      if (!response) throw new Error('Failed to start RTMP stream');
      
      const session = this.createSession(streamKey, response.hls_playlist_url, 'rtmp');
      await this.activateSession(session);
      
    } catch (error: any) {
      this.handleError(error);
    } finally {
      this.updateState({ isLoading: false });
    }
  }

  async stopCurrentStream(): Promise<void> {
    const currentSession = this.state.value.currentSession;
    if (!currentSession) return;

    this.updateState({ isLoading: true, error: null });
    
    try {
      // Stop backend stream
      await this.streamService.stopStream(currentSession.streamKey).toPromise();
      
      // Disconnect analysis service
      this.analysisService.disconnect();
      
      // Clear session
      this.clearSession();
      
    } catch (error: any) {
      this.handleError(error);
    } finally {
      this.updateState({ isLoading: false });
      this.loadAvailableStreams(); // Refresh stream list
    }
  }

  async createRtmpStream(name: string): Promise<void> {
    this.updateState({ isLoading: true, error: null });
    
    try {
      const stream = await this.streamService.createStream({
        name,
        source_type: 'rtmp',
        processing_mode: 'live'
      }).toPromise();
      
      if (stream) {
        await this.loadAvailableStreams();
      }
    } catch (error: any) {
      this.handleError(error);
    } finally {
      this.updateState({ isLoading: false });
    }
  }

  async deleteStream(streamId: number): Promise<void> {
    this.updateState({ isLoading: true, error: null });
    
    try {
      await this.streamService.deleteStream(streamId).toPromise();
      await this.loadAvailableStreams();
    } catch (error: any) {
      this.handleError(error);
    } finally {
      this.updateState({ isLoading: false });
    }
  }

  // Session Management
  private createSession(streamKey: string, hlsUrl: string, sourceType: 'webcam' | 'rtmp'): StreamSession {
    const session: StreamSession = {
      id: this.generateSessionId(),
      streamKey,
      hlsUrl: this.normalizeHlsUrl(hlsUrl),
      sourceType,
      startedAt: new Date()
    };
    
    this.persistSession(session);
    return session;
  }

  private async activateSession(session: StreamSession): Promise<void> {
    // Update state first
    this.updateState({ currentSession: session });
    
    // Connect to analysis WebSocket with session ID
    this.analysisService.connectToStream(session.streamKey, session.id);
    
    // Wait a moment for the stream to be ready
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Refresh available streams to show current status
    await this.loadAvailableStreams();
  }

  private clearSession(): void {
    localStorage.removeItem(this.SESSION_KEY);
    this.updateState({ currentSession: null });
  }

  private persistSession(session: StreamSession): void {
    localStorage.setItem(this.SESSION_KEY, JSON.stringify(session));
  }

  private restoreSession(): void {
    try {
      const stored = localStorage.getItem(this.SESSION_KEY);
      if (stored) {
        const session: StreamSession = JSON.parse(stored);
        // Only restore if session is recent (within last hour)
        const sessionAge = Date.now() - new Date(session.startedAt).getTime();
        if (sessionAge < 3600000) { // 1 hour
          this.updateState({ currentSession: session });
          this.analysisService.connectToStream(session.streamKey, session.id);
        } else {
          this.clearSession();
        }
      }
    } catch (error) {
      console.warn('Failed to restore session:', error);
      this.clearSession();
    }
  }

  // Utility Methods
  private async loadAvailableStreams(): Promise<void> {
    try {
      const response = await this.streamService.getStreams().toPromise();
      if (response) {
        this.updateState({ availableStreams: response.streams });
      }
    } catch (error) {
      console.error('Failed to load streams:', error);
    }
  }

  private normalizeHlsUrl(hlsUrl: string): string {
    // Convert backend URL to browser-accessible URL
    const filename = hlsUrl.split('/').pop() || '';
    return `/streaming/${filename}`;
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private updateState(partial: Partial<StreamState>): void {
    const current = this.state.value;
    this.state.next({ ...current, ...partial });
  }

  private handleError(error: any): void {
    let errorMessage = 'An unknown error occurred';
    
    if (error.status === 409) {
      errorMessage = error.error?.error || 'Stream conflict - another stream may be active';
    } else if (error.error?.error) {
      errorMessage = error.error.error;
    } else if (error.message) {
      errorMessage = error.message;
    }
    
    console.error('Stream operation error:', error);
    this.updateState({ error: errorMessage });
  }

  // Getters for current state
  getCurrentSession(): StreamSession | null {
    return this.state.value.currentSession;
  }

  getAvailableStreams(): Stream[] {
    return this.state.value.availableStreams;
  }

  isCurrentlyStreaming(): boolean {
    return !!this.state.value.currentSession;
  }
}