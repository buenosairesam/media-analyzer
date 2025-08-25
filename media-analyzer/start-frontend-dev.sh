#!/bin/bash

echo "🖥️  Starting Angular development server..."
echo ""

# Check if we're in the right directory
if [ ! -f "frontend/package.json" ]; then
  echo "❌ Error: Run this script from the media-analyzer root directory"
  exit 1
fi

# Check if backend services are running
if ! docker compose ps | grep -q "backend.*Up"; then
  echo "⚠️  Warning: Backend services don't appear to be running"
  echo "   Run './start-backend-only.sh' first to start backend services"
  echo ""
fi

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
  echo "📦 Installing npm dependencies..."
  npm install
  echo ""
fi

echo "🔥 Starting Angular dev server with hot reload..."
echo "   Frontend: http://localhost:4200"
echo "   Backend API: http://localhost:8000 (proxied)"
echo "   HLS Streaming: http://localhost:8081 (proxied)"
echo ""
echo "💡 Changes to TypeScript files will auto-reload!"
echo ""

# Start Angular dev server with proxy
ng serve --proxy-config proxy.conf.json --host 0.0.0.0 --port 4200