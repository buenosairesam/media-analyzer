#!/bin/bash
set -e

echo "Building images for ctlptl-registry deployment..."

REGISTRY="127.0.0.1:5005"

# Build backend image
echo "Building backend image..."
cd backend
docker build -t ${REGISTRY}/media-analyzer-backend:latest .
cd ..

# Build nginx image  
echo "Building nginx image..."
cd docker
docker build -f Dockerfile.nginx -t ${REGISTRY}/media-analyzer-nginx:latest .
cd ..

# Push to ctlptl registry
echo "Pushing images to ctlptl registry..."
docker push ${REGISTRY}/media-analyzer-backend:latest
docker push ${REGISTRY}/media-analyzer-nginx:latest

echo "✅ Images built and pushed to ctlptl registry!"
echo ""
echo "Images available:"
echo "- ${REGISTRY}/media-analyzer-backend:latest"
echo "- ${REGISTRY}/media-analyzer-nginx:latest"
echo ""
echo "Next: Update your K8s manifests to use these image names"