// Runtime environment configuration for Angular
// This can be loaded by the index.html before Angular starts
window.__env = window.__env || {};

// HLS streaming configuration - use existing streaming proxy
window.__env.HLS_BASE_URL = window.__env.HLS_BASE_URL || '/streaming/hls';
window.__env.API_URL = window.__env.API_URL || '/api';
window.__env.BACKEND_URL = window.__env.BACKEND_URL || '';