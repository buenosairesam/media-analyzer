import { Component, EventEmitter, Output } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { environment } from '../../../environments/environment';

interface Stream {
  id: number;
  name: string;
  source_type: string;
  processing_mode: string;
  status: string;
  stream_key: string;
  hls_playlist_url: string | null;
  rtmp_ingest_url: string;
  created_at: string;
}

@Component({
  selector: 'app-stream-control',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './stream-control.component.html',
  styleUrl: './stream-control.component.scss'
})
export class StreamControlComponent {
  @Output() streamSelected = new EventEmitter<string>();
  
  streams: Stream[] = [];
  newStreamName = '';
  selectedStream: Stream | null = null;

  constructor(private http: HttpClient) {
    this.loadStreams();
  }

  loadStreams() {
    this.http.get<{streams: Stream[]}>(`${environment.apiUrl}/streams/`).subscribe({
      next: (response) => {
        this.streams = response.streams;
      },
      error: (error) => console.error('Error loading streams:', error)
    });
  }

  createStream() {
    if (!this.newStreamName) return;

    this.http.post<Stream>(`${environment.apiUrl}/streams/create/`, {
      name: this.newStreamName,
      source_type: 'rtmp',
      processing_mode: 'live'
    }).subscribe({
      next: (stream) => {
        this.streams.push(stream);
        this.newStreamName = '';
      },
      error: (error) => console.error('Error creating stream:', error)
    });
  }

  startStream(stream: Stream) {
    this.http.post(`${environment.apiUrl}/streams/${stream.id}/start/`, {}).subscribe({
      next: () => {
        this.loadStreams();
      },
      error: (error) => console.error('Error starting stream:', error)
    });
  }

  stopStream(stream: Stream) {
    this.http.post(`${environment.apiUrl}/streams/${stream.id}/stop/`, {}).subscribe({
      next: () => {
        this.loadStreams();
      },
      error: (error) => console.error('Error stopping stream:', error)
    });
  }

  selectStream(stream: Stream) {
    this.selectedStream = stream;
    if (stream.hls_playlist_url) {
      // Use the HLS URL provided by backend - no hardcoding!
      this.streamSelected.emit(stream.hls_playlist_url);
    }
  }
}
