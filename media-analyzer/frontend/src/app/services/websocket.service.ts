import { Injectable } from '@angular/core';
import { Subject, Observable, BehaviorSubject } from 'rxjs';
import { Analysis } from '../models/analysis';

@Injectable({
  providedIn: 'root'
})
export class WebsocketService {
  private socket?: WebSocket;
  private analysisSubject = new Subject<Analysis>();
  private connectionStatus = new BehaviorSubject<boolean>(false);
  
  public analysis$ = this.analysisSubject.asObservable();
  public connectionStatus$ = this.connectionStatus.asObservable();

  constructor() { }

  connect(streamId: string) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = `ws://localhost:8000/ws/stream/${streamId}/`;
    console.log('Connecting to WebSocket:', wsUrl);
    
    this.socket = new WebSocket(wsUrl);
    
    this.socket.onopen = () => {
      console.log('WebSocket connected');
      this.connectionStatus.next(true);
    };
    
    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message:', data);
        
        if (data.type === 'analysis_update') {
          this.analysisSubject.next(data.analysis);
        } else if (data.type === 'recent_analysis') {
          data.analyses.forEach((analysis: Analysis) => {
            this.analysisSubject.next(analysis);
          });
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    this.socket.onclose = () => {
      console.log('WebSocket disconnected');
      this.connectionStatus.next(false);
    };
    
    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.connectionStatus.next(false);
    };
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = undefined;
      this.connectionStatus.next(false);
    }
  }

  send(message: any) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    }
  }

  ping() {
    this.send({
      type: 'ping',
      timestamp: Date.now()
    });
  }
}
