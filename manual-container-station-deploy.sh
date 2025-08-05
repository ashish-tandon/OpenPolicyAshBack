#!/bin/bash

# Manual Container Station Deployment Script
# Provides instructions for deploying via Container Station web interface
# Also builds and pushes Docker image to Docker Hub

set -e

# Configuration
QNAP_HOST="192.168.2.152"
DOCKER_USERNAME="ashishtandon"
IMAGE_NAME="openpolicy-single"
TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to build Docker image
build_docker_image() {
    log "Building Docker image..."
    
    # Check if Docker is available locally
    if ! command -v docker &> /dev/null; then
        error "Docker is not available locally"
        log "Please install Docker Desktop or Docker Engine first"
        return 1
    fi
    
    # Build the image
    log "Building image: ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"
    if docker build -f Dockerfile.single-container -t ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG} .; then
        success "Docker image built successfully"
        return 0
    else
        error "Failed to build Docker image"
        return 1
    fi
}

# Function to push Docker image to Docker Hub
push_docker_image() {
    log "Pushing Docker image to Docker Hub..."
    
    # Check if logged in to Docker Hub
    if ! docker info | grep -q "Username"; then
        warning "Not logged in to Docker Hub"
        log "Please run: docker login"
        log "Enter your Docker Hub credentials when prompted"
        return 1
    fi
    
    # Push the image
    log "Pushing image: ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"
    if docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}; then
        success "Docker image pushed successfully to Docker Hub"
        return 0
    else
        error "Failed to push Docker image to Docker Hub"
        return 1
    fi
}

# Function to create docker-compose file for manual deployment
create_docker_compose_file() {
    log "Creating docker-compose.yml for manual deployment..."
    
    cat > docker-compose.qnap.yml << EOF
version: '3.8'

services:
  openpolicy:
    image: ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}
    container_name: openpolicy_single
    ports:
      - "80:80"
      - "8000:8000"
      - "3000:3000"
      - "5555:5555"
      - "6379:6379"
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - DATABASE_URL=postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata
      - REDIS_URL=redis://localhost:6379/0
      - CORS_ORIGINS=http://localhost:3000,http://localhost:80,http://${QNAP_HOST},http://ashishsnas.myqnapcloud.com
      - NODE_ENV=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  postgres_data:
    driver: local
EOF

    success "docker-compose.yml created: docker-compose.qnap.yml"
}

# Function to show manual deployment instructions
show_manual_instructions() {
    log "Manual Container Station Deployment Instructions:"
    echo ""
    echo "🔧 Follow these steps to deploy via Container Station web interface:"
    echo ""
    echo "1. 📱 Open Container Station in your web browser:"
    echo "   http://${QNAP_HOST}:8080/container-station/"
    echo ""
    echo "2. 🔍 Click on 'Create' or 'Add Container'"
    echo ""
    echo "3. 📦 Choose 'Application' or 'Docker Compose'"
    echo ""
    echo "4. 📝 Copy and paste the following docker-compose configuration:"
    echo ""
    echo "---"
    cat docker-compose.qnap.yml
    echo "---"
    echo ""
    echo "5. 🚀 Click 'Create' or 'Deploy'"
    echo ""
    echo "6. ⏳ Wait for the container to start (this may take a few minutes)"
    echo ""
    echo "7. ✅ Verify the deployment by visiting:"
    echo "   http://${QNAP_HOST}/"
    echo ""
    echo "🔍 Alternative: Use 'Search' in Container Station"
    echo "1. Click 'Search' in Container Station"
    echo "2. Search for: ${DOCKER_USERNAME}/${IMAGE_NAME}"
    echo "3. Click 'Install' on the result"
    echo "4. Configure the ports and environment variables as shown above"
    echo ""
}

# Function to show access URLs
show_access_urls() {
    log "Access URLs after deployment:"
    echo ""
    echo "🌐 Main Dashboard: http://${QNAP_HOST}"
    echo "📊 API Documentation: http://${QNAP_HOST}:8000/docs"
    echo "🏥 Health Check: http://${QNAP_HOST}:8000/health"
    echo "🌺 Flower Monitor: http://${QNAP_HOST}:5555"
    echo "🗄️ Direct API: http://${QNAP_HOST}:8000"
    echo "🖥️ Direct Dashboard: http://${QNAP_HOST}:3000"
    echo ""
    echo "🌐 Domain Access (if available):"
    echo "🌐 Main Dashboard: https://ashishsnas.myqnapcloud.com"
    echo "📊 API Documentation: https://ashishsnas.myqnapcloud.com/api/docs"
    echo "🏥 Health Check: https://ashishsnas.myqnapcloud.com/health"
    echo ""
    echo "📱 Container Station Management:"
    echo "🔧 Container Station UI: http://${QNAP_HOST}:8080"
    echo "📊 Container Management: http://${QNAP_HOST}:8080/container-station/"
}

# Function to create deployment summary
create_summary() {
    log "Creating deployment summary..."
    
    TIMESTAMP=$(date +'%Y-%m-%d %H:%M:%S')
    
    cat > MANUAL_CONTAINER_STATION_DEPLOYMENT_${TIMESTAMP// /_}.md << EOF
# Manual Container Station Deployment Guide

**Deployment Date:** ${TIMESTAMP}
**QNAP Host:** ${QNAP_HOST}
**Docker Image:** ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}
**Method:** Manual Container Station Deployment

## Deployment Status

### ✅ Docker Image
- Image: ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}
- Status: Built and pushed to Docker Hub
- Ready for deployment

### 🔧 Container Station Deployment
- Method: Manual via web interface
- Status: Ready to deploy

## Deployment Steps

1. **Access Container Station:**
   - URL: http://${QNAP_HOST}:8080/container-station/

2. **Create Container:**
   - Click "Create" or "Add Container"
   - Choose "Application" or "Docker Compose"

3. **Use Configuration:**
   - Copy the docker-compose.yml content
   - Paste into Container Station

4. **Deploy:**
   - Click "Create" or "Deploy"
   - Wait for container to start

## Access URLs

### Local Network Access (IP)
- **Main Dashboard:** http://${QNAP_HOST}
- **API Documentation:** http://${QNAP_HOST}:8000/docs
- **Health Check:** http://${QNAP_HOST}:8000/health
- **Flower Monitor:** http://${QNAP_HOST}:5555

### Domain Access (if available)
- **Main Dashboard:** https://ashishsnas.myqnapcloud.com
- **API Documentation:** https://ashishsnas.myqnapcloud.com/api/docs
- **Health Check:** https://ashishsnas.myqnapcloud.com/health

## Services Included

1. **PostgreSQL Database** - Port 5432
2. **Redis Cache** - Port 6379
3. **FastAPI Backend** - Port 8000
4. **React Dashboard** - Port 3000
5. **Celery Worker** - Background
6. **Celery Beat** - Background
7. **Flower Monitor** - Port 5555
8. **Nginx Reverse Proxy** - Port 80

## Troubleshooting

- If container fails to start, check logs in Container Station
- Ensure all required ports are available
- Verify Docker image exists: ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}

## Next Steps

1. Deploy using Container Station web interface
2. Monitor container status
3. Verify all services are working
4. Set up regular backups

EOF

    success "Deployment summary created: MANUAL_CONTAINER_STATION_DEPLOYMENT_${TIMESTAMP// /_}.md"
}

# Main function
main() {
    log "🚀 Starting Manual Container Station Deployment Preparation"
    log "QNAP Host: ${QNAP_HOST}"
    log "Docker Image: ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"
    
    # Build Docker image
    if build_docker_image; then
        # Push to Docker Hub
        if push_docker_image; then
            success "Docker image is ready for deployment"
        else
            warning "Docker image built but not pushed to Docker Hub"
            log "You can still deploy using the local image"
        fi
    else
        error "Failed to build Docker image"
        log "Please check the Dockerfile and try again"
        exit 1
    fi
    
    # Create docker-compose file
    create_docker_compose_file
    
    # Show manual instructions
    show_manual_instructions
    
    # Show access URLs
    show_access_urls
    
    # Create summary
    create_summary
    
    log "🎉 Manual deployment preparation completed!"
    log "Follow the instructions above to deploy via Container Station web interface"
}

# Run main function
main "$@" 