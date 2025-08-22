#!/bin/bash

echo "🚀 Starting backend services only (excluding frontend)..."
echo "Frontend will run locally with 'ng serve' for faster development"
echo ""

# Start all services except frontend
docker compose up -d \
  postgres \
  redis \
  backend \
  celery-logo \
  celery-default \
  file-watcher \
  nginx-rtmp

echo ""
echo "✅ Backend services started!"
echo ""
echo "📋 Services running:"
echo "  - PostgreSQL:     localhost:5432"
echo "  - Redis:          localhost:6379"  
echo "  - Backend API:    localhost:8000"
echo "  - RTMP Server:    localhost:1935 (RTMP)"
echo "  - HLS Streaming:  localhost:8081 (HTTP)"
echo ""
echo "🔧 To start frontend development:"
echo "  cd frontend"
echo "  ng serve --proxy-config proxy.conf.json"
echo ""
echo "🌐 Frontend will be available at: http://localhost:4200"
echo ""
echo "📊 To check service status:"
echo "  docker compose ps"
echo ""
echo "📜 To view logs:"
echo "  docker compose logs -f [service-name]"