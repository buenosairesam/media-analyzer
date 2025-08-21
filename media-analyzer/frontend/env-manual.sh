#!/bin/bash

# Manual environment configuration for frontend development
# Source this file: source env-manual.sh

# HLS streaming configuration
export HLS_BASE_URL=${HLS_BASE_URL:-http://localhost:8081}
export API_URL=${API_URL:-/api}
export BACKEND_URL=${BACKEND_URL:-}

echo "Frontend environment configured:"
echo "  HLS_BASE_URL: $HLS_BASE_URL"
echo "  API_URL: $API_URL"
echo "  BACKEND_URL: $BACKEND_URL"

# For development with ng serve, you can also set these in env-config.js manually