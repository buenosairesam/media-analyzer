import { Component, ElementRef, Input, ViewChild, AfterViewInit, OnDestroy, OnChanges } from '@angular/core';
import Hls from 'hls.js';

@Component({
  selector: 'app-stream-viewer',
  standalone: true,
  imports: [],
  templateUrl: './stream-viewer.component.html',
  styleUrl: './stream-viewer.component.scss'
})
export class StreamViewerComponent implements AfterViewInit, OnDestroy, OnChanges {
  @ViewChild('video', { static: true }) videoElement!: ElementRef<HTMLVideoElement>;
  @Input() streamUrl: string = '';
  
  private hls?: Hls;

  ngAfterViewInit() {
    console.log('StreamViewer initialized with URL:', this.streamUrl);
    if (this.streamUrl) {
      this.loadStream(this.streamUrl);
    }
  }
  
  ngOnChanges() {
    console.log('StreamViewer URL changed to:', this.streamUrl);
    if (this.streamUrl && this.videoElement) {
      this.loadStream(this.streamUrl);
    }
  }

  ngOnDestroy() {
    if (this.hls) {
      this.hls.destroy();
    }
  }

  loadStream(url: string) {
    const video = this.videoElement.nativeElement;
    console.log('Loading HLS stream:', url);

    if (this.hls) {
      this.hls.destroy();
    }

    if (Hls.isSupported()) {
      this.hls = new Hls({
        debug: true,  // Enable debug logging
        enableWorker: false
      });
      
      this.hls.on(Hls.Events.MEDIA_ATTACHED, () => {
        console.log('HLS media attached');
      });
      
      this.hls.on(Hls.Events.MANIFEST_LOADED, () => {
        console.log('HLS manifest loaded');
      });
      
      this.hls.on(Hls.Events.ERROR, (event, data) => {
        console.error('HLS error:', data);
      });
      
      this.hls.loadSource(url);
      this.hls.attachMedia(video);
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      // Native HLS support (Safari)
      video.src = url;
    } else {
      console.error('HLS not supported');
    }
  }

  async play() {
    try {
      const video = this.videoElement.nativeElement;
      if (video.readyState >= 2) { // HAVE_CURRENT_DATA
        await video.play();
      } else {
        console.warn('Video not ready to play');
      }
    } catch (error) {
      console.error('Play error:', error);
    }
  }

  pause() {
    try {
      const video = this.videoElement.nativeElement;
      if (!video.paused) {
        video.pause();
      }
    } catch (error) {
      console.error('Pause error:', error);
    }
  }
}
