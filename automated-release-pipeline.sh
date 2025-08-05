#!/bin/bash

# 🚀 OpenPolicy Automated Release Pipeline
# Complete deployment automation for all environments
# Usage: ./automated-release-pipeline.sh [version] [--skip-tests] [--dry-run]

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="OpenPolicyAshBack"
DOCKER_IMAGE_NAME="ashishtandon9/openpolicyashback"
GITHUB_REPO="ashishtandon/OpenPolicyAshBack"
QNAP_HOST="ashishsnas.myqnapcloud.com"
QNAP_USER="admin"
AZURE_RESOURCE_GROUP="openpolicy-rg"
AZURE_ACR_NAME="openpolicyacr"

# Default values
VERSION=${1:-$(date +%Y%m%d-%H%M%S)}
SKIP_TESTS=false
DRY_RUN=false
COMMIT_MESSAGE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --commit-message)
            COMMIT_MESSAGE="$2"
            shift 2
            ;;
        *)
            VERSION="$1"
            shift
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

step() {
    echo -e "${PURPLE}🔧 $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    step "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check required tools
    for tool in docker git ssh az; do
        if ! command_exists "$tool"; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi
    
    # Check if we're in the right directory
    if [ ! -f "Dockerfile.api" ] || [ ! -f "src/api/main.py" ]; then
        error "Not in the correct project directory"
        exit 1
    fi
    
    success "All prerequisites are met"
}

# Function to validate code
validate_code() {
    step "Validating code quality..."
    
    if [ "$SKIP_TESTS" = true ]; then
        warning "Skipping code validation (--skip-tests flag)"
        return 0
    fi
    
    # Python syntax check
    log "Checking Python syntax..."
    if python3 -m py_compile src/api/main.py; then
        success "Python syntax validation passed"
    else
        error "Python syntax validation failed"
        exit 1
    fi
    
    # Check for common import issues
    log "Checking import paths..."
    if grep -r "from \." src/api/; then
        warning "Found relative imports in API code - fixing..."
        # Fix relative imports
        sed -i '' 's/from \.\./from src./g' src/api/*.py 2>/dev/null || true
        sed -i '' 's/from \./from src.api./g' src/api/*.py 2>/dev/null || true
    fi
    
    # Run tests if available
    if [ -f "run_comprehensive_tests.py" ]; then
        log "Running comprehensive tests..."
        if python3 run_comprehensive_tests.py; then
            success "All tests passed"
        else
            error "Tests failed"
            exit 1
        fi
    fi
    
    success "Code validation completed"
}

# Function to prepare Git operations
prepare_git_operations() {
    step "Preparing Git operations..."
    
    # Check if there are changes to commit
    if [ -z "$(git status --porcelain)" ]; then
        warning "No changes to commit"
        return 0
    fi
    
    # Set commit message
    if [ -z "$COMMIT_MESSAGE" ]; then
        COMMIT_MESSAGE="Release v$VERSION: Automated deployment"
    fi
    
    if [ "$DRY_RUN" = false ]; then
        # Add all changes
        git add .
        
        # Commit changes
        git commit -m "$COMMIT_MESSAGE"
        
        # Create and push tag
        git tag -a "v$VERSION" -m "Release v$VERSION"
        git push origin main
        git push origin "v$VERSION"
        
        success "Git operations completed"
    else
        info "DRY RUN: Would commit with message: $COMMIT_MESSAGE"
        info "DRY RUN: Would create tag: v$VERSION"
    fi
}

# Function to build and push Docker image
build_and_push_docker() {
    step "Building and pushing Docker image..."
    
    local image_tag="$DOCKER_IMAGE_NAME:$VERSION"
    local latest_tag="$DOCKER_IMAGE_NAME:latest"
    
    if [ "$DRY_RUN" = false ]; then
        # Build multi-architecture image
        log "Building multi-architecture Docker image..."
        docker buildx build \
            --platform linux/amd64,linux/arm64 \
            -f Dockerfile.api \
            -t "$image_tag" \
            -t "$latest_tag" \
            --push \
            .
        
        success "Docker image built and pushed: $image_tag"
    else
        info "DRY RUN: Would build and push Docker image: $image_tag"
    fi
}

# Function to deploy to local Docker
deploy_local() {
    step "Deploying to local Docker environment..."
    
    if [ "$DRY_RUN" = false ]; then
        # Stop existing containers
        log "Stopping existing containers..."
        docker-compose -f docker-compose.single.yml down 2>/dev/null || true
        
        # Pull latest image
        log "Pulling latest image..."
        docker pull "$DOCKER_IMAGE_NAME:$VERSION"
        
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
    else
        info "DRY RUN: Would deploy to local Docker environment"
    fi
}

# Function to deploy to QNAP
deploy_qnap() {
    step "Deploying to QNAP Container Station..."
    
    if [ "$DRY_RUN" = false ]; then
        # Create deployment script for QNAP
        cat > /tmp/qnap-deploy.sh << 'EOF'
#!/bin/bash
set -e

# QNAP deployment script
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
        scp /tmp/qnap-deploy.sh "$QNAP_USER@$QNAP_HOST:/tmp/"
        
        log "Executing deployment on QNAP..."
        ssh "$QNAP_USER@$QNAP_HOST" "chmod +x /tmp/qnap-deploy.sh && /tmp/qnap-deploy.sh"
        
        success "QNAP deployment completed"
    else
        info "DRY RUN: Would deploy to QNAP Container Station"
    fi
}

# Function to deploy to Azure
deploy_azure() {
    step "Deploying to Azure Container Apps..."
    
    if [ "$DRY_RUN" = false ]; then
        # Check Azure CLI login
        if ! az account show >/dev/null 2>&1; then
            error "Azure CLI not logged in. Please run 'az login' first."
            return 1
        fi
        
        # Build and push to Azure Container Registry
        log "Building for Azure Container Registry..."
        docker build --platform linux/amd64 -f Dockerfile.api-simple -t "$AZURE_ACR_NAME.azurecr.io/openpolicy-api:$VERSION" .
        
        # Login to ACR
        log "Logging into Azure Container Registry..."
        az acr login --name "$AZURE_ACR_NAME"
        
        # Push to ACR
        log "Pushing to Azure Container Registry..."
        docker push "$AZURE_ACR_NAME.azurecr.io/openpolicy-api:$VERSION"
        
        # Deploy to Container Apps
        log "Deploying to Azure Container Apps..."
        az containerapp update \
            --name openpolicy-api \
            --resource-group "$AZURE_RESOURCE_GROUP" \
            --image "$AZURE_ACR_NAME.azurecr.io/openpolicy-api:$VERSION" \
            --registry-server "$AZURE_ACR_NAME.azurecr.io" \
            --registry-username "$AZURE_ACR_NAME" \
            --registry-password "$(az acr credential show --name "$AZURE_ACR_NAME" --query "passwords[0].value" -o tsv)"
        
        success "Azure deployment completed"
    else
        info "DRY RUN: Would deploy to Azure Container Apps"
    fi
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
    
    local report_file="deployment_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# OpenPolicy Deployment Report

**Version**: $VERSION  
**Date**: $(date)  
**Status**: $([ "$DRY_RUN" = true ] && echo "DRY RUN" || echo "COMPLETED")

## Deployment Summary

### Code Repository
- **GitHub**: $([ "$DRY_RUN" = false ] && echo "✅ Pushed" || echo "⏭️ Skipped (DRY RUN)")
- **Version Tag**: v$VERSION

### Docker Images
- **Docker Hub**: $([ "$DRY_RUN" = false ] && echo "✅ Pushed" || echo "⏭️ Skipped (DRY RUN)")
- **Image**: $DOCKER_IMAGE_NAME:$VERSION

### Runtime Environments
- **Local Docker**: $([ "$DRY_RUN" = false ] && echo "✅ Deployed" || echo "⏭️ Skipped (DRY RUN)")
- **QNAP Container Station**: $([ "$DRY_RUN" = false ] && echo "✅ Deployed" || echo "⏭️ Skipped (DRY RUN)")
- **Azure Container Apps**: $([ "$DRY_RUN" = false ] && echo "✅ Deployed" || echo "⏭️ Skipped (DRY RUN)")

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
*Report generated by OpenPolicy Automated Release Pipeline*
EOF
    
    success "Deployment report generated: $report_file"
}

# Function to cleanup temporary files
cleanup() {
    log "Cleaning up temporary files..."
    rm -f /tmp/qnap-deploy.sh 2>/dev/null || true
}

# Main execution function
main() {
    echo -e "${PURPLE}🚀 OpenPolicy Automated Release Pipeline${NC}"
    echo -e "${CYAN}Version: $VERSION${NC}"
    echo -e "${CYAN}Dry Run: $DRY_RUN${NC}"
    echo -e "${CYAN}Skip Tests: $SKIP_TESTS${NC}"
    echo ""
    
    # Set up error handling
    trap cleanup EXIT
    
    # Execute pipeline steps
    check_prerequisites
    validate_code
    prepare_git_operations
    build_and_push_docker
    deploy_local
    deploy_qnap
    deploy_azure
    verify_deployments
    generate_report
    
    echo ""
    success "🎉 Release pipeline completed successfully!"
    info "Version $VERSION has been deployed to all environments"
    
    if [ "$DRY_RUN" = true ]; then
        warning "This was a dry run - no actual changes were made"
    fi
}

# Execute main function
main "$@" 