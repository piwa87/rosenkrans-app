import { HttpClient } from '@angular/common/http';
import { Injectable, signal, OnDestroy } from '@angular/core';
import { RosaryState } from '../models/rosary-state.model';

@Injectable({
  providedIn: 'root',
})
export class RosaryStateService implements OnDestroy {
  private readonly _state = signal<RosaryState | null>(null);
  readonly state = this._state.asReadonly();

  private eventSource: EventSource | null = null;

  constructor(private http: HttpClient) {}

  /** Fetch the current state and connect the SSE stream. */
  connect(): void {
    this.http
      .get<RosaryState>('/state')
      .subscribe((s) => this._state.set(s));

    this.openStream();
  }

  private openStream(): void {
    this.eventSource = new EventSource('/stream');

    this.eventSource.onmessage = (ev: MessageEvent) => {
      try {
        this._state.set(JSON.parse(ev.data) as RosaryState);
      } catch (e) {
        console.error('SSE parse error', e);
      }
    };

    this.eventSource.onerror = () => {
      console.log('SSE disconnected — retrying in 2 s…');
      this.eventSource?.close();
      this.eventSource = null;
      setTimeout(() => this.openStream(), 2000);
    };
  }

  ngOnDestroy(): void {
    this.eventSource?.close();
  }
}
