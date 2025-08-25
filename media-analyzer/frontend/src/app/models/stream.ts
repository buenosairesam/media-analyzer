export interface Stream {
  id: number;
  name: string;
  source_type: 'rtmp' | 'webcam' | 'file' | 'url';
  processing_mode: 'live' | 'batch';
  status: 'inactive' | 'starting' | 'active' | 'stopping' | 'error';
  stream_key: string;
  hls_playlist_url?: string;
  rtmp_ingest_url?: string;
  created_at: string;
}
