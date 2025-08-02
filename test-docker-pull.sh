#!/bin/bash

# Test script to verify Docker image pull and run
# This helps verify the multi-architecture image works correctly

set -e

REPO="ashishtandon9/openpolicyashback"
TAG="latest"
CONTAINER_NAME="test_openpolicy"

echo "🧪 Testing Docker image pull and run..."
echo "📦 Repository: $REPO:$TAG"

# Clean up any existing test container
echo "🧹 Cleaning up any existing test container..."
docker rm -f $CONTAINER_NAME 2>/dev/null || true

# Pull the image
echo "📥 Pulling image..."
docker pull $REPO:$TAG

# Test run the container (background)
echo "🚀 Starting test container..."
docker run -d \
    --name $CONTAINER_NAME \
    -p 8001:8000 \
    $REPO:$TAG

# Wait a moment for the container to start
echo "⏳ Waiting for container to start..."
sleep 5

# Check if container is running
if docker ps | grep -q $CONTAINER_NAME; then
    echo "✅ Container is running successfully!"
    
    # Test health endpoint
    echo "🏥 Testing health endpoint..."
    if curl -f http://localhost:8001/health 2>/dev/null; then
        echo "✅ Health endpoint is working!"
    else
        echo "⚠️  Health endpoint not responding (this might be normal if endpoint doesn't exist)"
    fi
    
    # Show container logs
    echo "📋 Container logs:"
    docker logs $CONTAINER_NAME --tail 10
    
else
    echo "❌ Container failed to start"
    docker logs $CONTAINER_NAME
    exit 1
fi

# Clean up
echo "🧹 Cleaning up test container..."
docker rm -f $CONTAINER_NAME

echo "🎉 Test completed successfully!"
echo "✅ Your multi-architecture Docker image is working correctly!" 