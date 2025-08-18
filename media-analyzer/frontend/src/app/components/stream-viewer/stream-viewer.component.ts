import { Component, ElementRef, Input, ViewChild, AfterViewInit, OnDestroy, OnChanges } from '@angular/core';
import Hls from 'hls.js';
import { Analysis, DetectionResult } from '../../models/analysis';

@Component({
  selector: 'app-stream-viewer',
  standalone: true,
  imports: [],
  templateUrl: './stream-viewer.component.html',
  styleUrl: './stream-viewer.component.scss'
})
export class StreamViewerComponent implements AfterViewInit, OnDestroy, OnChanges {
  @ViewChild('video', { static: true }) videoElement!: ElementRef<HTMLVideoElement>;
  @ViewChild('overlay', { static: true }) overlayElement!: ElementRef<HTMLCanvasElement>;
  @Input() streamUrl: string = '';
  @Input() detections: DetectionResult[] = [];
  
  showOverlay = true;
  private hls?: Hls;
  private ctx?: CanvasRenderingContext2D;

  ngAfterViewInit() {
    this.setupCanvas();
    if (this.streamUrl) {
      this.loadStream(this.streamUrl);
    }
  }
  
  ngOnChanges() {
    if (this.streamUrl && this.videoElement) {
      this.loadStream(this.streamUrl);
    }
    
    // Redraw detections when they change
    if (this.ctx) {
      this.drawDetections();
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
        debug: false,
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

  toggleOverlay() {
    this.showOverlay = !this.showOverlay;
    if (this.showOverlay) {
      this.drawDetections();
    } else {
      this.clearOverlay();
    }
  }

  private setupCanvas() {
    const video = this.videoElement.nativeElement;
    const canvas = this.overlayElement.nativeElement;
    this.ctx = canvas.getContext('2d')!;
    
    // Sync canvas size with video
    const resizeCanvas = () => {
      canvas.width = video.clientWidth;
      canvas.height = video.clientHeight;
      canvas.style.width = video.clientWidth + 'px';
      canvas.style.height = video.clientHeight + 'px';
      this.drawDetections();
    };
    
    video.addEventListener('loadedmetadata', resizeCanvas);
    video.addEventListener('resize', resizeCanvas);
    window.addEventListener('resize', resizeCanvas);
  }

  private drawDetections() {
    if (!this.ctx || !this.showOverlay) return;
    
    this.clearOverlay();
    
    const canvas = this.overlayElement.nativeElement;
    const video = this.videoElement.nativeElement;
    
    // Draw each detection
    this.detections.forEach(detection => {
      this.drawDetection(detection, canvas.width, canvas.height);
    });
  }

  private drawDetection(detection: DetectionResult, canvasWidth: number, canvasHeight: number) {
    if (!this.ctx) return;
    
    // Convert normalized bbox to canvas coordinates
    const x = detection.bbox.x * canvasWidth;
    const y = detection.bbox.y * canvasHeight;
    const width = detection.bbox.width * canvasWidth;
    const height = detection.bbox.height * canvasHeight;
    
    // Color by detection type
    const colors = {
      'object': '#00ff00',
      'logo': '#ff0000', 
      'text': '#0000ff'
    };
    const color = colors[detection.detection_type] || '#ffffff';
    
    // Draw bounding box
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = 2;
    this.ctx.strokeRect(x, y, width, height);
    
    // Draw label
    this.ctx.fillStyle = color;
    this.ctx.font = '14px Arial';
    const label = `${detection.label} (${Math.round(detection.confidence * 100)}%)`;
    const textWidth = this.ctx.measureText(label).width;
    
    // Background for text
    this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    this.ctx.fillRect(x, y - 20, textWidth + 8, 20);
    
    // Text
    this.ctx.fillStyle = color;
    this.ctx.fillText(label, x + 4, y - 6);
  }

  private clearOverlay() {
    if (!this.ctx) return;
    const canvas = this.overlayElement.nativeElement;
    this.ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
}
