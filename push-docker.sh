#!/bin/bash

# Docker Build and Push Script for OpenPolicyAshBack (Multi-Architecture)
# Usage: ./push-docker.sh [version]
# Supports both AMD64 and ARM64 architectures

set -e

# Default version if not provided
VERSION=${1:-latest}
REPO="ashishtandon9/openpolicyashback"

echo "🚀 Building multi-architecture Docker image..."
echo "📋 Platforms: linux/amd64, linux/arm64"
echo "🏷️  Tag: $REPO:$VERSION"

# Build and push multi-architecture image
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -f Dockerfile.api \
    -t $REPO:$VERSION \
    --push \
    .

echo "✅ Successfully pushed multi-architecture image $REPO:$VERSION to Docker Hub!"
echo "🔗 View your image at: https://hub.docker.com/r/$REPO"
echo "📱 This image now supports both AMD64 and ARM64 architectures (including QNAP servers)" 