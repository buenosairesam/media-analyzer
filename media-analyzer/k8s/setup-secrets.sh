#!/bin/bash
set -e

echo "Setting up Kubernetes secrets..."

# Create namespace first
kubectl create namespace media-analyzer --dry-run=client -o yaml | kubectl apply -f -

# Django secrets
echo "Creating Django secrets..."
kubectl create secret generic django-secrets \
  --from-literal=secret-key="$(openssl rand -base64 32)" \
  --namespace=media-analyzer \
  --dry-run=client -o yaml | kubectl apply -f -

# PostgreSQL secrets  
echo "Creating PostgreSQL secrets..."
kubectl create secret generic postgres-secrets \
  --from-literal=username=media_user \
  --from-literal=password="$(openssl rand -base64 16)" \
  --namespace=media-analyzer \
  --dry-run=client -o yaml | kubectl apply -f -

# GCP credentials (if file exists)
if [ -f "credentials.json" ]; then
    echo "Creating GCP credentials secret..."
    kubectl create secret generic gcp-credentials \
      --from-file=credentials.json=credentials.json \
      --namespace=media-analyzer \
      --dry-run=client -o yaml | kubectl apply -f -
    echo "✅ GCP credentials loaded"
else
    echo "⚠️  credentials.json not found - creating placeholder secret"
    echo "To enable GCP features:"
    echo "1. Download GCP service account key as 'credentials.json'"
    echo "2. Run: kubectl create secret generic gcp-credentials --from-file=credentials.json=credentials.json -n media-analyzer"
    
    # Create empty secret as placeholder
    kubectl create secret generic gcp-credentials \
      --from-literal=credentials.json='{}' \
      --namespace=media-analyzer \
      --dry-run=client -o yaml | kubectl apply -f -
fi

echo ""
echo "Secrets created in namespace 'media-analyzer':"
kubectl get secrets -n media-analyzer

echo ""
echo "🎯 Ready for deployment!"
echo "Next: kubectl apply -k k8s/overlays/development"