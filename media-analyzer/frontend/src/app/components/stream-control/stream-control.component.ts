import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { StreamService } from '../../services/stream.service';
import { Stream } from '../../models/stream';

@Component({
  selector: 'app-stream-control',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './stream-control.component.html',
  styleUrl: './stream-control.component.scss'
})
export class StreamControlComponent {
  @Output() streamSelected = new EventEmitter<string>();
  @Output() streamStopped = new EventEmitter<void>();
  
  streams: Stream[] = [];
  newStreamName = '';
  selectedStream: Stream | null = null;
  activeTab: 'rtmp' | 'webcam' = 'webcam';

  constructor(private streamService: StreamService) {
    this.loadStreams();
  }

  loadStreams() {
    this.streamService.getStreams().subscribe({
      next: (response) => {
        this.streams = response.streams;
      },
      error: (error) => console.error('Error loading streams:', error)
    });
  }

  createStream() {
    if (!this.newStreamName) return;

    this.streamService.createStream({
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
    this.streamService.startStream(stream.id).subscribe({
      next: () => {
        this.loadStreams();
      },
      error: (error) => console.error('Error starting stream:', error)
    });
  }

  stopStream(stream: Stream) {
    this.streamService.stopStream(stream.id).subscribe({
      next: () => {
        this.loadStreams();
        // Emit event to clear the player
        this.streamStopped.emit();
      },
      error: (error) => console.error('Error stopping stream:', error)
    });
  }

  startWebcam() {
    this.streamService.startWebcamStream().subscribe({
      next: (stream) => {
        this.loadStreams();
        // Backend now waits for HLS to be ready, so we can directly select
        this.selectStream(stream);
      },
      error: (error) => {
        console.error('Error starting webcam:', error);
        if (error.status === 409) {
          alert(`Cannot start webcam: ${error.error.error}`);
        }
      }
    });
  }

  switchTab(tab: 'rtmp' | 'webcam') {
    this.activeTab = tab;
  }

  get rtmpStreams() {
    return this.streams.filter(stream => stream.source_type === 'rtmp');
  }

  get webcamStreams() {
    return this.streams.filter(stream => stream.source_type === 'webcam');
  }

  selectStream(stream: Stream) {
    this.selectedStream = stream;
    if (stream.hls_playlist_url) {
      // Use the HLS URL provided by backend - no hardcoding!
      this.streamSelected.emit(stream.hls_playlist_url);
    }
  }
}
