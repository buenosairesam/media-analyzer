import { Component, ElementRef, Input, ViewChild, AfterViewInit, OnDestroy } from '@angular/core';
import Hls from 'hls.js';

@Component({
  selector: 'app-stream-viewer',
  standalone: true,
  imports: [],
  templateUrl: './stream-viewer.component.html',
  styleUrl: './stream-viewer.component.scss'
})
export class StreamViewerComponent implements AfterViewInit, OnDestroy {
  @ViewChild('video', { static: true }) videoElement!: ElementRef<HTMLVideoElement>;
  @Input() streamUrl: string = '';
  
  private hls?: Hls;

  ngAfterViewInit() {
    if (this.streamUrl) {
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

    if (Hls.isSupported()) {
      this.hls = new Hls();
      this.hls.loadSource(url);
      this.hls.attachMedia(video);
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      // Native HLS support (Safari)
      video.src = url;
    } else {
      console.error('HLS not supported');
    }
  }

  play() {
    this.videoElement.nativeElement.play();
  }

  pause() {
    this.videoElement.nativeElement.pause();
  }
}
