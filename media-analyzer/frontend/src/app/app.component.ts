import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';
import { StreamControlComponent } from './components/stream-control/stream-control.component';
import { StreamViewerComponent } from './components/stream-viewer/stream-viewer.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, HttpClientModule, StreamControlComponent, StreamViewerComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  title = 'Media Analyzer';
  selectedStreamUrl: string = '';

  onStreamSelected(streamUrl: string) {
    this.selectedStreamUrl = streamUrl;
  }
}
