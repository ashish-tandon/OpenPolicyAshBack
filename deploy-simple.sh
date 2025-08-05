#!/bin/bash

# 🚀 Simple OpenPolicy Deployment
# Deploy using the Azure Container Registry image (SQLite-based)
# Usage: ./deploy-simple.sh

set -e

# Configuration
DOCKER_IMAGE="ashishtandon9/openpolicyashback:latest"
QNAP_HOST="ashishsnas.myqnapcloud.com"
QNAP_USER="admin"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
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

step() {
    echo -e "${PURPLE}🔧 $1${NC}"
}

# Function to deploy to local Docker
deploy_local() {
    step "Deploying to local Docker environment..."
    
    # Stop existing containers
    log "Stopping existing containers..."
    docker stop openpolicy_simple 2>/dev/null || true
    docker rm openpolicy_simple 2>/dev/null || true
    
    # Pull Docker Hub image
    log "Pulling Docker Hub image..."
    docker pull --platform linux/amd64 "$DOCKER_IMAGE"
    
    # Start container
    log "Starting container..."
    docker run -d \
        --name openpolicy_simple \
        --restart unless-stopped \
        --platform linux/amd64 \
        -p 8000:8000 \
        -v "$(pwd)/data:/app/data" \
        "$DOCKER_IMAGE"
    
    # Wait for health check
    log "Waiting for health check..."
    sleep 15
    
    # Verify deployment
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        success "Local deployment successful"
    else
        error "Local deployment failed - health check failed"
        return 1
    fi
}

# Function to deploy to QNAP
deploy_qnap() {
    step "Deploying to QNAP Container Station..."
    
    # Create deployment script for QNAP
    cat > /tmp/qnap-deploy-simple.sh << EOF
#!/bin/bash
set -e

# QNAP deployment script using Docker Hub image
CONTAINER_NAME="openpolicy_simple"
IMAGE_NAME="$DOCKER_IMAGE"

echo "Stopping existing container..."
docker stop \$CONTAINER_NAME 2>/dev/null || true
docker rm \$CONTAINER_NAME 2>/dev/null || true

echo "Pulling Docker Hub image..."
docker pull \$IMAGE_NAME

echo "Starting container..."
docker run -d \\
    --name \$CONTAINER_NAME \\
    --restart unless-stopped \\
    -p 8000:8000 \\
    -v /share/Container/openpolicy:/app/data \\
    \$IMAGE_NAME

echo "Waiting for health check..."
sleep 20

echo "Verifying deployment..."
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "QNAP deployment successful"
else
    echo "QNAP deployment failed"
    exit 1
fi
EOF
    
    # Copy and execute deployment script on QNAP
    log "Copying deployment script to QNAP..."
    scp /tmp/qnap-deploy-simple.sh "$QNAP_USER@$QNAP_HOST:/tmp/"
    
    log "Executing deployment on QNAP..."
    ssh "$QNAP_USER@$QNAP_HOST" "chmod +x /tmp/qnap-deploy-simple.sh && /tmp/qnap-deploy-simple.sh"
    
    success "QNAP deployment completed"
}

# Function to verify deployments
verify_deployments() {
    step "Verifying all deployments..."
    
    local failed_deployments=()
    
    # Check local deployment
    log "Checking local deployment..."
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        success "Local deployment verified"
    else
        failed_deployments+=("Local")
    fi
    
    # Check QNAP deployment
    log "Checking QNAP deployment..."
    if ssh "$QNAP_USER@$QNAP_HOST" "curl -f http://localhost:8000/health >/dev/null 2>&1"; then
        success "QNAP deployment verified"
    else
        failed_deployments+=("QNAP")
    fi
    
    if [ ${#failed_deployments[@]} -eq 0 ]; then
        success "All deployments verified successfully"
    else
        warning "Some deployments failed verification: ${failed_deployments[*]}"
    fi
}

# Function to generate deployment report
generate_report() {
    step "Generating deployment report..."
    
    local report_file="deployment_report_simple_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# OpenPolicy Simple Deployment Report

**Date**: $(date)  
**Status**: COMPLETED

## Deployment Summary

### Docker Image Used
- **Docker Hub**: $DOCKER_IMAGE

### Runtime Environments
- **Local Docker**: ✅ Deployed
- **QNAP Container Station**: ✅ Deployed

## Health Check Results

### Local Environment
- **URL**: http://localhost:8000/health
- **Status**: $(curl -f http://localhost:8000/health >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Failed")

### QNAP Environment
- **URL**: http://$QNAP_HOST:8000/health
- **Status**: $(ssh "$QNAP_USER@$QNAP_HOST" "curl -f http://localhost:8000/health >/dev/null 2>&1" && echo "✅ Healthy" || echo "❌ Failed")

## API Endpoints

### Health Check
- **GET** http://localhost:8000/health

### API Endpoints
- **GET** http://localhost:8000/api/health
- **GET** http://localhost:8000/api/stats
- **GET** http://localhost:8000/api/jurisdictions
- **GET** http://localhost:8000/api/representatives
- **GET** http://localhost:8000/api/bills

## Next Steps

1. Test API endpoints
2. Monitor application performance
3. Check error logs for any issues
4. Verify all features are working correctly

---
*Report generated by OpenPolicy Simple Deployment Script*
EOF
    
    success "Deployment report generated: $report_file"
}

# Function to cleanup temporary files
cleanup() {
    log "Cleaning up temporary files..."
    rm -f /tmp/qnap-deploy-simple.sh 2>/dev/null || true
}

# Main execution function
main() {
    echo -e "${PURPLE}🚀 OpenPolicy Simple Deployment${NC}"
    echo ""
    
    # Set up error handling
    trap cleanup EXIT
    
    # Execute deployment steps
    deploy_local
    deploy_qnap
    verify_deployments
    generate_report
    
    echo ""
    success "🎉 Simple deployment completed successfully!"
    echo ""
    echo -e "${BLUE}📊 Access URLs:${NC}"
    echo "Local: http://localhost:8000/health"
    echo "QNAP: http://$QNAP_HOST:8000/health"
    echo ""
    echo -e "${BLUE}📋 API Documentation:${NC}"
    echo "API Docs: http://localhost:8000/docs"
    echo "ReDoc: http://localhost:8000/redoc"
}

# Execute main function
main "$@" 