# Media Analyzer

Real-time video streaming and AI analysis platform that demonstrates modern cloud-native architecture and machine learning integration. The system ingests RTMP video streams (from sources like OBS), processes them with computer vision AI models, and provides live analysis results through a responsive web dashboard.

## Features

- **Video Ingestion**: Accept RTMP streams and convert to HLS for web playback
- **AI Processing**: Real-time object detection (YOLO) and scene analysis (CLIP) on video segments
- **Live Dashboard**: Angular frontend with WebSocket-powered real-time analysis overlays
- **Scalable Architecture**: Kubernetes-deployed microservices with configurable processing modes
- **Cloud Integration**: GCP services integration while maintaining platform agnostic design

## Tech Stack

- **Backend**: Django + Django Channels, PostgreSQL, Redis, Celery
- **AI/ML**: OpenCV, YOLO, CLIP, Whisper (Hugging Face Transformers)
- **Frontend**: Angular 17+ with HLS.js video player and Canvas overlays
- **Infrastructure**: Docker containers, Kubernetes, NGINX
- **Streaming**: FFmpeg for RTMP’HLS conversion, WebSocket for real-time data

## Quick Start

### Option 1: Docker Compose (Development)

```bash
# Start all services
docker compose up

# Run migrations (in separate terminal)
docker compose --profile tools up migrate

# Access the application
# Frontend: http://localhost:4200
# Backend API: http://localhost:8000
# RTMP Stream: rtmp://localhost:1935/live
# HLS Stream: http://localhost:8081/hls
```

### Option 2: Kubernetes (Production-ready)

```bash
# Build and push images to local registry
./k8s/build-for-ctlptl.sh

# Deploy to Kubernetes
kubectl apply -k k8s/overlays/development

# Check deployment status
kubectl get pods -n media-analyzer

# Access via port forwarding
kubectl port-forward service/frontend -n media-analyzer 4200:80
```

## Architecture

- **Django Backend**: Main API server with WebSocket support for real-time communication
- **Celery Workers**: Distributed task processing for AI analysis (logo detection, visual analysis)
- **PostgreSQL**: Primary database for application data and analysis results
- **Redis**: Cache and message broker for Celery tasks
- **Angular Frontend**: Single-page application with real-time video analysis overlays
- **NGINX RTMP**: Stream ingestion server for OBS and other RTMP sources

## Development

The system supports both local development with hot reload and production deployment:

- **Development**: Uses Angular dev server and Django development server
- **Production**: Uses nginx for static files and optimized Docker images

## Demo

Stream video from OBS Studio to `rtmp://localhost:1935/live` and watch real-time AI analysis in the web dashboard with live object detection overlays.