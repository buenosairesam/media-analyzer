#!/bin/bash
set -e

echo "Building images for ctlptl-registry deployment..."

# Use KIND network DNS name for registry (assumes ctlptl-registry is connected to kind network)
REGISTRY="ctlptl-registry:5000"

# Ensure registry is connected to KIND network
echo "Connecting registry to KIND network..."
docker network connect kind ctlptl-registry 2>/dev/null || echo "Registry already connected to KIND network"

# Build backend image
echo "Building backend image..."
cd backend
docker build -t 127.0.0.1:5005/media-analyzer-backend:latest .
# Tag for KIND network access
docker tag 127.0.0.1:5005/media-analyzer-backend:latest ${REGISTRY}/media-analyzer-backend:latest
cd ..

# Build frontend image (production build)
echo "Building frontend image..."
cd frontend
docker build --target production -t 127.0.0.1:5005/media-analyzer-frontend:latest .
# Tag for KIND network access
docker tag 127.0.0.1:5005/media-analyzer-frontend:latest ${REGISTRY}/media-analyzer-frontend:latest
cd ..

# Build nginx image  
echo "Building nginx image..."
cd docker
docker build -f Dockerfile.nginx -t 127.0.0.1:5005/media-analyzer-nginx:latest .
# Tag for KIND network access
docker tag 127.0.0.1:5005/media-analyzer-nginx:latest ${REGISTRY}/media-analyzer-nginx:latest
cd ..

# Push to ctlptl registry using localhost address (which supports HTTPS)
echo "Pushing images to ctlptl registry..."
docker push 127.0.0.1:5005/media-analyzer-backend:latest
docker push 127.0.0.1:5005/media-analyzer-frontend:latest
docker push 127.0.0.1:5005/media-analyzer-nginx:latest

echo "✅ Images built and pushed to ctlptl registry!"
echo ""
echo "Images available:"
echo "- ${REGISTRY}/media-analyzer-backend:latest"
echo "- ${REGISTRY}/media-analyzer-frontend:latest"
echo "- ${REGISTRY}/media-analyzer-nginx:latest"
echo ""
echo "Ready to deploy with: kubectl apply -k k8s/overlays/development"