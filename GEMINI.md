# Media Analyzer

## Project Overview

This project is a real-time video streaming and AI analysis platform. It ingests RTMP video streams, processes them with computer vision AI models, and provides live analysis results through a responsive web dashboard.

The architecture is based on microservices and includes:

*   **Backend**: A Django application that handles video stream management, AI processing, and WebSocket communication for real-time updates.
*   **Frontend**: An Angular single-page application that provides a user interface for stream viewing and analysis visualization.
*   **AI Processing**: A Python-based analysis engine that uses various adapters for different types of analysis, such as object detection, logo detection, and motion analysis. The engine can be configured to run locally, on a remote LAN worker, or in the cloud.
*   **Streaming**: An NGINX server with the RTMP module ingests video streams and converts them to HLS for web playback.
*   **Infrastructure**: The entire platform is containerized using Docker and can be deployed with Docker Compose for development or Kubernetes for production.

## Building and Running

### Docker Compose (Development)

To run the application in a development environment, use Docker Compose:

```bash
# Start all services
docker compose up

# Run migrations (in a separate terminal)
docker compose --profile tools up migrate
```

The application will be accessible at the following URLs:

*   **Frontend**: `http://localhost:4200`
*   **Backend API**: `http://localhost:8000`
*   **RTMP Stream**: `rtmp://localhost:1935/live`
*   **HLS Stream**: `http://localhost:8081/hls`

### Kubernetes (Production-like)

To deploy the application to a Kubernetes cluster, you can use the provided scripts:

```bash
# Build and push images to a local registry
./k8s/build-for-ctlptl.sh

# Deploy to Kubernetes
kubectl apply -k k8s/overlays/development

# Check deployment status
kubectl get pods -n media-analyzer

# Access the application via port forwarding
kubectl port-forward service/frontend -n media-analyzer 4200:80
```

## Development Conventions

*   **Backend**: The backend is a Django application. Follow Django best practices for development.
*   **Frontend**: The frontend is an Angular application. Follow Angular best practices for development.
*   **AI Processing**: The AI processing engine is designed to be extensible. To add a new analysis capability, create a new adapter and integrate it with the `AnalysisEngine`.
*   **Testing**: The project includes a `test_unified_ai.py` file, which suggests that there is a testing framework in place. Run existing tests and add new ones when making changes.
