import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Stream } from '../models/stream';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class StreamService {
  private apiUrl = `${environment.apiUrl}/streaming`;

  constructor(private http: HttpClient) { }

  getStreams(): Observable<{streams: Stream[]}> {
    return this.http.get<{streams: Stream[]}>(`${this.apiUrl}/streams/`);
  }

  createStream(streamData: any): Observable<Stream> {
    return this.http.post<Stream>(`${this.apiUrl}/streams/create/`, streamData);
  }

  startWebcamStream(): Observable<Stream> {
    return this.http.post<Stream>(`${this.apiUrl}/streams/webcam/start/`, {});
  }

  startStream(streamKey: string): Observable<{message: string, hls_playlist_url: string}> {
    return this.http.post<{message: string, hls_playlist_url: string}>(`${this.apiUrl}/streams/${streamKey}/start/`, {});
  }

  stopStream(streamKey: string): Observable<{message: string}> {
    return this.http.post<{message: string}>(`${this.apiUrl}/streams/${streamKey}/stop/`, {});
  }

  deleteStream(streamId: number): Observable<{message: string}> {
    return this.http.delete<{message: string}>(`${this.apiUrl}/streams/${streamId}/`);
  }
}
