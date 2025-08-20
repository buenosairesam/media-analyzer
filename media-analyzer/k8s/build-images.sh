#!/bin/bash
set -e

echo "Building Docker images for Kubernetes deployment..."

# Build backend image with AI processing capabilities
echo "Building backend image..."
cd backend
docker build -t media-analyzer-backend:latest .
cd ..

# Build nginx image for HLS streaming (if using local storage)
echo "Building nginx image..."
cd docker
docker build -f Dockerfile.nginx -t media-analyzer-nginx:latest .
cd ..

# Load images into KIND cluster (if running)
if command -v kind &> /dev/null && kind get clusters | grep -q "media-analyzer"; then
    echo "Loading images into KIND cluster..."
    kind load docker-image media-analyzer-backend:latest --name media-analyzer
    kind load docker-image media-analyzer-nginx:latest --name media-analyzer
    echo "Images loaded into KIND cluster"
else
    echo "KIND cluster 'media-analyzer' not found - images built locally only"
fi

echo "Docker images built successfully!"
echo ""
echo "Images built:"
echo "- media-analyzer-backend:latest  (Django + Celery + AI processing)"
echo "- media-analyzer-nginx:latest    (RTMP/HLS streaming)"
echo ""
echo "Next steps:"
echo "1. Create KIND cluster: kind create cluster --name media-analyzer"
echo "2. Deploy to K8s: kubectl apply -k k8s/overlays/development"