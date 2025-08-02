#!/bin/bash

# Docker Hub Push Commands for OpenPolicy Backend
# Run these commands on your local machine where Docker is installed

echo "Building and pushing OpenPolicy images to Docker Hub..."

# Your Docker Hub username
DOCKER_USER="ashishtandon9"

# 1. Build the policy validator image
echo "Building policy validator image..."
docker build -t ${DOCKER_USER}/openpolicyashback-policy-validator:latest \
    -f Dockerfile.policy-validator .

# 2. Build the celery worker image (using main Dockerfile)
echo "Building celery worker image..."
docker build -t ${DOCKER_USER}/openpolicyashback-celery:latest \
    -f Dockerfile .

# 3. Push policy validator image
echo "Pushing policy validator image..."
docker push ${DOCKER_USER}/openpolicyashback-policy-validator:latest

# 4. Push celery worker image
echo "Pushing celery worker image..."
docker push ${DOCKER_USER}/openpolicyashback-celery:latest

# 5. Tag main image if not already tagged
echo "Ensuring main image is properly tagged..."
docker tag ${DOCKER_USER}/openpolicyashback:latest ${DOCKER_USER}/openpolicyashback:$(date +%Y%m%d)
docker push ${DOCKER_USER}/openpolicyashback:$(date +%Y%m%d)

echo "✅ All images pushed successfully!"
echo ""
echo "Published images:"
echo "  - ${DOCKER_USER}/openpolicyashback:latest"
echo "  - ${DOCKER_USER}/openpolicyashback-policy-validator:latest"
echo "  - ${DOCKER_USER}/openpolicyashback-celery:latest"