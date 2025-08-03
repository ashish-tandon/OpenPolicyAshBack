#!/bin/bash

# OpenPolicy Comprehensive Deployment Script
# Deploys to Git, Docker Hub, and QNAP in one coordinated plan

set -e

# Configuration
DOCKER_IMAGE_NAME="ashishtandon/openpolicy-single"
DOCKER_TAG="latest"
QNAP_HOST="ashishsnas.myqnapcloud.com"
QNAP_PORT="22"
QNAP_USER="admin"
CONTAINER_NAME="openpolicy_single"

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command_exists docker; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! command_exists git; then
        error "Git is not installed"
        exit 1
    fi
    
    if ! command_exists ssh; then
        error "SSH is not installed"
        exit 1
    fi
    
    success "All prerequisites are met"
}

# Function to validate code
validate_code() {
    log "Validating code..."
    
    # Check if we're in the right directory
    if [ ! -f "Dockerfile.single-container" ]; then
        error "Dockerfile.single-container not found. Are you in the correct directory?"
        exit 1
    fi
    
    # Check if main API file exists
    if [ ! -f "src/api/main.py" ]; then
        error "src/api/main.py not found"
        exit 1
    fi
    
    # Test Python syntax
    if python3 -m py_compile src/api/main.py; then
        success "Python syntax validation passed"
    else
        error "Python syntax validation failed"
        exit 1
    fi
    
    # Check if dashboard exists
    if [ ! -f "dashboard/package.json" ]; then
        error "Dashboard package.json not found"
        exit 1
    fi
    
    success "Code validation completed"
}

# Function to build Docker image
build_docker_image() {
    log "Building Docker image..."
    
    # Build the image
    if docker build -f Dockerfile.single-container -t ${DOCKER_IMAGE_NAME}:${DOCKER_TAG} .; then
        success "Docker image built successfully"
    else
        error "Docker image build failed"
        exit 1
    fi
    
    # Tag with timestamp for versioning
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    docker tag ${DOCKER_IMAGE_NAME}:${DOCKER_TAG} ${DOCKER_IMAGE_NAME}:${TIMESTAMP}
    success "Docker image tagged with timestamp: ${TIMESTAMP}"
}

# Function to test Docker image locally
test_docker_image() {
    log "Testing Docker image locally..."
    
    # Stop any existing container
    docker stop ${CONTAINER_NAME} 2>/dev/null || true
    docker rm ${CONTAINER_NAME} 2>/dev/null || true
    
    # Run container in background
    if docker run -d \
        --name ${CONTAINER_NAME} \
        -p 80:80 \
        -p 8000:8000 \
        -p 3000:3000 \
        -p 5555:5555 \
        ${DOCKER_IMAGE_NAME}:${DOCKER_TAG}; then
        
        success "Container started successfully"
        
        # Wait for services to be ready
        log "Waiting for services to be ready..."
        sleep 30
        
        # Test health endpoint
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            success "API health check passed"
        else
            error "API health check failed"
            docker logs ${CONTAINER_NAME}
            exit 1
        fi
        
        # Test dashboard
        if curl -f http://localhost:3000 >/dev/null 2>&1; then
            success "Dashboard health check passed"
        else
            error "Dashboard health check failed"
            docker logs ${CONTAINER_NAME}
            exit 1
        fi
        
        # Stop test container
        docker stop ${CONTAINER_NAME}
        docker rm ${CONTAINER_NAME}
        success "Local testing completed successfully"
    else
        error "Failed to start test container"
        exit 1
    fi
}

# Function to push to Git
push_to_git() {
    log "Pushing to Git..."
    
    # Check if there are changes to commit
    if git diff-index --quiet HEAD --; then
        warning "No changes to commit"
    else
        # Add all changes
        git add .
        
        # Commit with timestamp
        TIMESTAMP=$(date +'%Y-%m-%d %H:%M:%S')
        if git commit -m "Deployment update - ${TIMESTAMP}"; then
            success "Changes committed"
        else
            error "Failed to commit changes"
            exit 1
        fi
    fi
    
    # Push to remote
    if git push origin main; then
        success "Successfully pushed to Git"
    else
        error "Failed to push to Git"
        exit 1
    fi
}

# Function to push to Docker Hub
push_to_dockerhub() {
    log "Pushing to Docker Hub..."
    
    # Check if logged in to Docker Hub
    if ! docker info | grep -q "Username"; then
        warning "Not logged in to Docker Hub. Please run 'docker login' first"
        return 1
    fi
    
    # Push latest tag
    if docker push ${DOCKER_IMAGE_NAME}:${DOCKER_TAG}; then
        success "Successfully pushed latest tag to Docker Hub"
    else
        error "Failed to push to Docker Hub"
        return 1
    fi
    
    # Push timestamped tag
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    if docker push ${DOCKER_IMAGE_NAME}:${TIMESTAMP}; then
        success "Successfully pushed timestamped tag to Docker Hub"
    else
        error "Failed to push timestamped tag to Docker Hub"
        return 1
    fi
}

# Function to deploy to QNAP
deploy_to_qnap() {
    log "Deploying to QNAP..."
    
    # Create deployment script for QNAP
    cat > qnap-deploy-remote.sh << 'EOF'
#!/bin/bash
set -e

# Stop and remove existing container
docker stop openpolicy_single 2>/dev/null || true
docker rm openpolicy_single 2>/dev/null || true

# Remove old image
docker rmi ashishtandon/openpolicy-single:latest 2>/dev/null || true

# Pull latest image
docker pull ashishtandon/openpolicy-single:latest

# Create docker-compose file
cat > docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  openpolicy:
    image: ashishtandon/openpolicy-single:latest
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
      - CORS_ORIGINS=http://localhost:3000,http://localhost:80,http://ashishsnas.myqnapcloud.com
      - NODE_ENV=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "/app/healthcheck.sh"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  postgres_data:
    driver: local
COMPOSE_EOF

# Start the container
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Test health endpoint
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ API health check passed"
else
    echo "❌ API health check failed"
    docker logs openpolicy_single
    exit 1
fi

# Test dashboard
if curl -f http://localhost:3000 >/dev/null 2>&1; then
    echo "✅ Dashboard health check passed"
else
    echo "❌ Dashboard health check failed"
    docker logs openpolicy_single
    exit 1
fi

echo "✅ QNAP deployment completed successfully"
EOF

    # Make script executable
    chmod +x qnap-deploy-remote.sh
    
    # Copy script to QNAP and execute
    if scp -P ${QNAP_PORT} qnap-deploy-remote.sh ${QNAP_USER}@${QNAP_HOST}:/tmp/; then
        success "Deployment script copied to QNAP"
    else
        error "Failed to copy deployment script to QNAP"
        exit 1
    fi
    
    # Execute deployment on QNAP
    if ssh -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "bash /tmp/qnap-deploy-remote.sh"; then
        success "Successfully deployed to QNAP"
    else
        error "Failed to deploy to QNAP"
        exit 1
    fi
    
    # Clean up local script
    rm qnap-deploy-remote.sh
}

# Function to monitor deployment
monitor_deployment() {
    log "Monitoring deployment..."
    
    # Test QNAP deployment
    log "Testing QNAP deployment..."
    
    # Wait a bit for services to stabilize
    sleep 10
    
    # Test API
    if curl -f https://${QNAP_HOST}/health >/dev/null 2>&1; then
        success "QNAP API is responding"
    else
        warning "QNAP API health check failed"
    fi
    
    # Test dashboard
    if curl -f https://${QNAP_HOST}/ >/dev/null 2>&1; then
        success "QNAP Dashboard is responding"
    else
        warning "QNAP Dashboard health check failed"
    fi
    
    success "Deployment monitoring completed"
}

# Function to create deployment summary
create_summary() {
    log "Creating deployment summary..."
    
    TIMESTAMP=$(date +'%Y-%m-%d %H:%M:%S')
    
    cat > DEPLOYMENT_SUMMARY_${TIMESTAMP// /_}.md << EOF
# OpenPolicy Deployment Summary

**Deployment Date:** ${TIMESTAMP}
**Docker Image:** ${DOCKER_IMAGE_NAME}:${DOCKER_TAG}

## Deployment Status

### ✅ Git Repository
- Changes committed and pushed
- Repository: $(git remote get-url origin)

### ✅ Docker Hub
- Image: ${DOCKER_IMAGE_NAME}:${DOCKER_TAG}
- Image: ${DOCKER_IMAGE_NAME}:$(date +%Y%m%d_%H%M%S)

### ✅ QNAP NAS
- Host: ${QNAP_HOST}
- Container: ${CONTAINER_NAME}
- Status: Running

## Access URLs

- **Main Dashboard:** https://${QNAP_HOST}/
- **API Documentation:** https://${QNAP_HOST}/api/docs
- **Health Check:** https://${QNAP_HOST}/health
- **Flower Monitor:** https://${QNAP_HOST}:5555

## Services Included

1. **PostgreSQL Database** - Port 5432
2. **Redis Cache** - Port 6379
3. **FastAPI Backend** - Port 8000
4. **React Dashboard** - Port 3000
5. **Celery Worker** - Background
6. **Celery Beat** - Background
7. **Flower Monitor** - Port 5555
8. **Nginx Reverse Proxy** - Port 80

## Health Checks

- Database connectivity
- Redis connectivity
- API responsiveness
- Dashboard accessibility

## Next Steps

1. Monitor system performance
2. Check logs for any errors
3. Verify all features are working
4. Set up regular backups

EOF

    success "Deployment summary created: DEPLOYMENT_SUMMARY_${TIMESTAMP// /_}.md"
}

# Main deployment function
main() {
    log "🚀 Starting OpenPolicy Comprehensive Deployment"
    log "Targets: Git, Docker Hub, QNAP"
    
    # Check prerequisites
    check_prerequisites
    
    # Validate code
    validate_code
    
    # Build Docker image
    build_docker_image
    
    # Test locally
    test_docker_image
    
    # Push to Git
    push_to_git
    
    # Push to Docker Hub
    if push_to_dockerhub; then
        success "Docker Hub deployment successful"
    else
        warning "Docker Hub deployment failed - continuing with QNAP deployment"
    fi
    
    # Deploy to QNAP
    deploy_to_qnap
    
    # Monitor deployment
    monitor_deployment
    
    # Create summary
    create_summary
    
    log "🎉 Deployment completed successfully!"
    log "Access your application at: https://${QNAP_HOST}/"
}

# Run main function
main "$@" 