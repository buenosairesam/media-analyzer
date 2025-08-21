declare global {
  interface Window {
    __env?: {
      HLS_BASE_URL?: string;
      API_URL?: string;
      BACKEND_URL?: string;
    };
  }
}

export const environment = {
  production: false,
  // Use runtime env vars with defaults
  apiUrl: (window as any).__env?.API_URL || '/api',
  backendUrl: (window as any).__env?.BACKEND_URL || '',
  hlsBaseUrl: (window as any).__env?.HLS_BASE_URL || 'http://localhost:8081',
};