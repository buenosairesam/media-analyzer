#!/bin/bash
# Remote Docker Build Script for NVIDIA Machine
# 
# This script builds Docker images on a remote NVIDIA machine for faster
# PyTorch/CUDA compilation, then transfers them back to the local machine.
#
# Prerequisites:
# 1. SSH key-based auth to remote machine
# 2. Docker installed and user in docker group on remote
# 3. KIND cluster running locally (optional - for auto-loading)
#
# Manual troubleshooting:
# - SSH access: ssh mcrndeb "docker ps"
# - Docker perms: ssh mcrndeb "sudo usermod -aG docker $USER" (then logout/login)
# - Build manually: ssh mcrndeb "cd /tmp/media-analyzer-build/backend && docker build ."

set -e

NVIDIA_HOST="mcrndeb"
REMOTE_DIR="/tmp/media-analyzer-build"

echo "Building Docker images on NVIDIA machine ($NVIDIA_HOST)..."

# Copy source code to NVIDIA machine
echo "Copying source code to $NVIDIA_HOST..."
ssh $NVIDIA_HOST "mkdir -p $REMOTE_DIR"

# Create a temporary archive excluding large directories
echo "Creating source archive..."
tar --exclude='.git' --exclude='venv' --exclude='node_modules' --exclude='postgres_data' --exclude='*.tar.gz' -czf media-analyzer-src.tar.gz .

# Copy and extract on remote machine
echo "Transferring and extracting source..."
scp media-analyzer-src.tar.gz $NVIDIA_HOST:$REMOTE_DIR/
ssh $NVIDIA_HOST "cd $REMOTE_DIR && tar -xzf media-analyzer-src.tar.gz"

# Cleanup local archive
rm media-analyzer-src.tar.gz

# Build backend image on NVIDIA machine
echo "Building backend image on $NVIDIA_HOST..."
ssh $NVIDIA_HOST "cd $REMOTE_DIR/backend && docker build -t media-analyzer-backend:latest ."

# Build nginx image on NVIDIA machine
echo "Building nginx image on $NVIDIA_HOST..."
ssh $NVIDIA_HOST "cd $REMOTE_DIR/docker && docker build -f Dockerfile.nginx -t media-analyzer-nginx:latest ."

# Save images to tar files
echo "Saving images to tar files..."
ssh $NVIDIA_HOST "docker save media-analyzer-backend:latest | gzip > $REMOTE_DIR/backend-image.tar.gz"
ssh $NVIDIA_HOST "docker save media-analyzer-nginx:latest | gzip > $REMOTE_DIR/nginx-image.tar.gz"

# Copy images back to local machine
echo "Copying images back to local machine..."
scp $NVIDIA_HOST:$REMOTE_DIR/backend-image.tar.gz ./
scp $NVIDIA_HOST:$REMOTE_DIR/nginx-image.tar.gz ./

# Load images locally
echo "Loading images into local Docker..."
gunzip -c backend-image.tar.gz | docker load
gunzip -c nginx-image.tar.gz | docker load

# Load into KIND cluster if it exists
if kind get clusters | grep -q "media-analyzer"; then
    echo "Loading images into KIND cluster..."
    kind load docker-image media-analyzer-backend:latest --name media-analyzer
    kind load docker-image media-analyzer-nginx:latest --name media-analyzer
    echo "Images loaded into KIND cluster"
else
    echo "KIND cluster 'media-analyzer' not found - images available locally only"
fi

# Cleanup
echo "Cleaning up..."
rm -f backend-image.tar.gz nginx-image.tar.gz
ssh $NVIDIA_HOST "rm -rf $REMOTE_DIR"

echo "✅ Remote build complete!"
echo ""
echo "Images built and loaded:"
echo "- media-analyzer-backend:latest"
echo "- media-analyzer-nginx:latest"