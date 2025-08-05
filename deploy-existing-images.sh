#!/bin/bash

# 🚀 OpenPolicy Deployment Using Existing Images
# Deploy to all environments using pre-built Docker images
# Usage: ./deploy-existing-images.sh

set -e

# Configuration
DOCKER_IMAGE_NAME="ashishtandon9/openpolicyashback"
QNAP_HOST="ashishsnas.myqnapcloud.com"
QNAP_USER="admin"
AZURE_RESOURCE_GROUP="openpolicy-rg"
AZURE_ACR_NAME="openpolicyacr"

# Colors for output
RED='\033[0;31m'
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
    docker-compose -f docker-compose.single.yml down 2>/dev/null || true
    
    # Pull latest image
    log "Pulling latest image..."
    docker pull "$DOCKER_IMAGE_NAME:latest"
    
    # Start containers
    log "Starting containers..."
    docker-compose -f docker-compose.single.yml up -d
    
    # Wait for health check
    log "Waiting for health check..."
    sleep 10
    
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
    cat > /tmp/qnap-deploy-existing.sh << 'EOF'
#!/bin/bash
set -e

# QNAP deployment script using existing image
CONTAINER_NAME="openpolicy_single"
IMAGE_NAME="ashishtandon9/openpolicyashback:latest"

echo "Stopping existing container..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

echo "Pulling latest image..."
docker pull $IMAGE_NAME

echo "Starting new container..."
docker run -d \
    --name $CONTAINER_NAME \
    --restart unless-stopped \
    -p 8000:8000 \
    -v /share/Container/openpolicy:/app/data \
    $IMAGE_NAME

echo "Waiting for health check..."
sleep 15

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
    scp /tmp/qnap-deploy-existing.sh "$QNAP_USER@$QNAP_HOST:/tmp/"
    
    log "Executing deployment on QNAP..."
    ssh "$QNAP_USER@$QNAP_HOST" "chmod +x /tmp/qnap-deploy-existing.sh && /tmp/qnap-deploy-existing.sh"
    
    success "QNAP deployment completed"
}

# Function to deploy to Azure
deploy_azure() {
    step "Deploying to Azure Container Apps..."
    
    # Check Azure CLI login
    if ! az account show >/dev/null 2>&1; then
        error "Azure CLI not logged in. Please run 'az login' first."
        return 1
    fi
    
    # Use existing image from ACR
    log "Using existing Azure Container Registry image..."
    
    # Deploy to Container Apps
    log "Deploying to Azure Container Apps..."
    az containerapp update \
        --name openpolicy-api \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --image "$AZURE_ACR_NAME.azurecr.io/openpolicy-api:latest" \
        --registry-server "$AZURE_ACR_NAME.azurecr.io" \
        --registry-username "$AZURE_ACR_NAME" \
        --registry-password "$(az acr credential show --name "$AZURE_ACR_NAME" --query "passwords[0].value" -o tsv)"
    
    success "Azure deployment completed"
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
    
    # Check Azure deployment
    log "Checking Azure deployment..."
    local azure_url=$(az containerapp show --name openpolicy-api --resource-group "$AZURE_RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null)
    if [ -n "$azure_url" ] && curl -f "https://$azure_url/health" >/dev/null 2>&1; then
        success "Azure deployment verified"
    else
        failed_deployments+=("Azure")
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
    
    local report_file="deployment_report_existing_images_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# OpenPolicy Deployment Report (Existing Images)

**Date**: $(date)  
**Status**: COMPLETED

## Deployment Summary

### Docker Images Used
- **Docker Hub**: $DOCKER_IMAGE_NAME:latest
- **Azure ACR**: $AZURE_ACR_NAME.azurecr.io/openpolicy-api:latest

### Runtime Environments
- **Local Docker**: ✅ Deployed
- **QNAP Container Station**: ✅ Deployed
- **Azure Container Apps**: ✅ Deployed

## Health Check Results

### Local Environment
- **URL**: http://localhost:8000/health
- **Status**: $(curl -f http://localhost:8000/health >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Failed")

### QNAP Environment
- **URL**: http://$QNAP_HOST:8000/health
- **Status**: $(ssh "$QNAP_USER@$QNAP_HOST" "curl -f http://localhost:8000/health >/dev/null 2>&1" && echo "✅ Healthy" || echo "❌ Failed")

### Azure Environment
- **URL**: https://$(az containerapp show --name openpolicy-api --resource-group "$AZURE_RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null)/health
- **Status**: $(curl -f "https://$(az containerapp show --name openpolicy-api --resource-group "$AZURE_RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null)/health" >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Failed")

## Next Steps

1. Monitor application performance
2. Check error logs for any issues
3. Verify all features are working correctly
4. Update documentation if needed

---
*Report generated by OpenPolicy Deployment Script (Existing Images)*
EOF
    
    success "Deployment report generated: $report_file"
}

# Function to cleanup temporary files
cleanup() {
    log "Cleaning up temporary files..."
    rm -f /tmp/qnap-deploy-existing.sh 2>/dev/null || true
}

# Main execution function
main() {
    echo -e "${PURPLE}🚀 OpenPolicy Deployment Using Existing Images${NC}"
    echo ""
    
    # Set up error handling
    trap cleanup EXIT
    
    # Execute deployment steps
    deploy_local
    deploy_qnap
    deploy_azure
    verify_deployments
    generate_report
    
    echo ""
    success "🎉 Deployment completed successfully!"
    info "All environments deployed using existing Docker images"
}

# Execute main function
main "$@" 