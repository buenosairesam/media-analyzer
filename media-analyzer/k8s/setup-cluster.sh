#!/bin/bash
set -e

CLUSTER_NAME="media-analyzer"

echo "Setting up KIND cluster for Media Analyzer..."

# Check if cluster already exists
if kind get clusters | grep -q "$CLUSTER_NAME"; then
    echo "Cluster '$CLUSTER_NAME' already exists"
    echo "Delete it? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Deleting existing cluster..."
        kind delete cluster --name "$CLUSTER_NAME"
    else
        echo "Using existing cluster"
    fi
fi

# Create KIND cluster with ingress support
if ! kind get clusters | grep -q "$CLUSTER_NAME"; then
    echo "Creating KIND cluster '$CLUSTER_NAME'..."
    cat <<EOF | kind create cluster --name "$CLUSTER_NAME" --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 8080
    protocol: TCP
  - containerPort: 443
    hostPort: 8443
    protocol: TCP
EOF
fi

# Install nginx ingress controller
echo "Installing nginx ingress controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for ingress controller to be ready
echo "Waiting for ingress controller to be ready..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

echo "KIND cluster setup complete!"
echo ""
echo "Cluster info:"
kubectl cluster-info --context kind-$CLUSTER_NAME
echo ""
echo "Next steps:"
echo "1. Build images: ./k8s/build-images.sh"
echo "2. Setup secrets: ./k8s/setup-secrets.sh"  
echo "3. Deploy application: kubectl apply -k k8s/overlays/development"