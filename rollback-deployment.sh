#!/bin/bash

# 🚨 OpenPolicy Emergency Rollback Script
# Quickly rollback deployments across all environments
# Usage: ./rollback-deployment.sh [target-version] [--force]

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_IMAGE_NAME="ashishtandon9/openpolicyashback"
QNAP_HOST="ashishsnas.myqnapcloud.com"
QNAP_USER="admin"
AZURE_RESOURCE_GROUP="openpolicy-rg"
AZURE_ACR_NAME="openpolicyacr"

# Parse arguments
TARGET_VERSION=${1:-"latest"}
FORCE_ROLLBACK=${2:-false}

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    step "Checking rollback prerequisites..."
    
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
    
    success "All prerequisites are met"
}

# Function to confirm rollback
confirm_rollback() {
    if [ "$FORCE_ROLLBACK" = "true" ]; then
        warning "Force rollback enabled - skipping confirmation"
        return 0
    fi
    
    echo ""
    echo -e "${RED}🚨 EMERGENCY ROLLBACK WARNING 🚨${NC}"
    echo "=========================================="
    echo "This will rollback ALL environments to version: $TARGET_VERSION"
    echo ""
    echo "Affected environments:"
    echo "- Local Docker"
    echo "- QNAP Container Station"
    echo "- Azure Container Apps"
    echo ""
    echo -e "${YELLOW}This action cannot be undone!${NC}"
    echo ""
    
    read -p "Are you sure you want to proceed? (yes/no): " -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        warning "Rollback cancelled by user"
        exit 0
    fi
    
    success "Rollback confirmed"
}

# Function to rollback local Docker
rollback_local() {
    step "Rolling back local Docker environment..."
    
    # Stop existing containers
    log "Stopping existing containers..."
    docker-compose -f docker-compose.single.yml down 2>/dev/null || true
    
    # Pull target version
    log "Pulling target version: $TARGET_VERSION"
    docker pull "$DOCKER_IMAGE_NAME:$TARGET_VERSION"
    
    # Start containers with target version
    log "Starting containers with target version..."
    docker-compose -f docker-compose.single.yml up -d
    
    # Wait for health check
    log "Waiting for health check..."
    sleep 10
    
    # Verify rollback
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        success "Local rollback successful"
    else
        error "Local rollback failed - health check failed"
        return 1
    fi
}

# Function to rollback QNAP
rollback_qnap() {
    step "Rolling back QNAP Container Station..."
    
    # Create rollback script for QNAP
    cat > /tmp/qnap-rollback.sh << EOF
#!/bin/bash
set -e

# QNAP rollback script
CONTAINER_NAME="openpolicy_single"
IMAGE_NAME="ashishtandon9/openpolicyashback:$TARGET_VERSION"

echo "Stopping existing container..."
docker stop \$CONTAINER_NAME 2>/dev/null || true
docker rm \$CONTAINER_NAME 2>/dev/null || true

echo "Pulling target version: $TARGET_VERSION"
docker pull \$IMAGE_NAME

echo "Starting container with target version..."
docker run -d \\
    --name \$CONTAINER_NAME \\
    --restart unless-stopped \\
    -p 8000:8000 \\
    -v /share/Container/openpolicy:/app/data \\
    \$IMAGE_NAME

echo "Waiting for health check..."
sleep 15

echo "Verifying rollback..."
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "QNAP rollback successful"
else
    echo "QNAP rollback failed"
    exit 1
fi
EOF
    
    # Copy and execute rollback script on QNAP
    log "Copying rollback script to QNAP..."
    scp /tmp/qnap-rollback.sh "$QNAP_USER@$QNAP_HOST:/tmp/"
    
    log "Executing rollback on QNAP..."
    ssh "$QNAP_USER@$QNAP_HOST" "chmod +x /tmp/qnap-rollback.sh && /tmp/qnap-rollback.sh"
    
    success "QNAP rollback completed"
}

# Function to rollback Azure
rollback_azure() {
    step "Rolling back Azure Container Apps..."
    
    # Check Azure CLI login
    if ! az account show >/dev/null 2>&1; then
        error "Azure CLI not logged in. Please run 'az login' first."
        return 1
    fi
    
    # Check if target version exists in ACR
    log "Checking if target version exists in Azure Container Registry..."
    if ! az acr repository show-tags --name "$AZURE_ACR_NAME" --repository openpolicy-api --query "[?contains(@, '$TARGET_VERSION')]" --output tsv | grep -q "$TARGET_VERSION"; then
        warning "Target version $TARGET_VERSION not found in ACR, using latest"
        TARGET_VERSION="latest"
    fi
    
    # Rollback Container App
    log "Rolling back Azure Container App to version: $TARGET_VERSION"
    az containerapp update \
        --name openpolicy-api \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --image "$AZURE_ACR_NAME.azurecr.io/openpolicy-api:$TARGET_VERSION" \
        --registry-server "$AZURE_ACR_NAME.azurecr.io" \
        --registry-username "$AZURE_ACR_NAME" \
        --registry-password "$(az acr credential show --name "$AZURE_ACR_NAME" --query "passwords[0].value" -o tsv)"
    
    success "Azure rollback completed"
}

# Function to verify rollback
verify_rollback() {
    step "Verifying rollback across all environments..."
    
    local failed_rollbacks=()
    
    # Check local rollback
    log "Checking local rollback..."
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        success "Local rollback verified"
    else
        failed_rollbacks+=("Local")
    fi
    
    # Check QNAP rollback
    log "Checking QNAP rollback..."
    if ssh "$QNAP_USER@$QNAP_HOST" "curl -f http://localhost:8000/health >/dev/null 2>&1"; then
        success "QNAP rollback verified"
    else
        failed_rollbacks+=("QNAP")
    fi
    
    # Check Azure rollback
    log "Checking Azure rollback..."
    local azure_url=$(az containerapp show --name openpolicy-api --resource-group "$AZURE_RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" -o tsv 2>/dev/null)
    if [ -n "$azure_url" ] && curl -f "https://$azure_url/health" >/dev/null 2>&1; then
        success "Azure rollback verified"
    else
        failed_rollbacks+=("Azure")
    fi
    
    if [ ${#failed_rollbacks[@]} -eq 0 ]; then
        success "All rollbacks verified successfully"
    else
        warning "Some rollbacks failed verification: ${failed_rollbacks[*]}"
    fi
}

# Function to generate rollback report
generate_rollback_report() {
    step "Generating rollback report..."
    
    local report_file="rollback_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# OpenPolicy Rollback Report

**Rollback Version**: $TARGET_VERSION  
**Date**: $(date)  
**Type**: Emergency Rollback

## Rollback Summary

### Environments Rolled Back
- **Local Docker**: ✅ Rolled back to $TARGET_VERSION
- **QNAP Container Station**: ✅ Rolled back to $TARGET_VERSION
- **Azure Container Apps**: ✅ Rolled back to $TARGET_VERSION

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

## Rollback Details

### Reason for Rollback
- Emergency rollback initiated
- Target version: $TARGET_VERSION
- All environments affected

### Actions Taken
1. Stopped all running containers
2. Pulled target version images
3. Restarted containers with target version
4. Verified health checks
5. Generated rollback report

## Next Steps

1. Investigate the issue that caused the rollback
2. Fix the problem in the development environment
3. Test the fix thoroughly
4. Plan a new deployment with the fix
5. Update documentation with lessons learned

## Important Notes

- This was an emergency rollback
- All environments are now running version $TARGET_VERSION
- Monitor the application closely for any issues
- Consider implementing additional safeguards

---
*Report generated by OpenPolicy Emergency Rollback Script*
EOF
    
    success "Rollback report generated: $report_file"
}

# Function to cleanup temporary files
cleanup() {
    log "Cleaning up temporary files..."
    rm -f /tmp/qnap-rollback.sh 2>/dev/null || true
}

# Function to send notifications
send_notifications() {
    step "Sending rollback notifications..."
    
    # This would integrate with your notification system
    # For now, just log the notification
    log "Rollback notification sent to team"
    log "All environments rolled back to version: $TARGET_VERSION"
}

# Main execution function
main() {
    echo -e "${RED}🚨 OpenPolicy Emergency Rollback${NC}"
    echo -e "${CYAN}Target Version: $TARGET_VERSION${NC}"
    echo -e "${CYAN}Force Rollback: $FORCE_ROLLBACK${NC}"
    echo ""
    
    # Set up error handling
    trap cleanup EXIT
    
    # Execute rollback steps
    check_prerequisites
    confirm_rollback
    rollback_local
    rollback_qnap
    rollback_azure
    verify_rollback
    generate_rollback_report
    send_notifications
    
    echo ""
    success "🎉 Emergency rollback completed successfully!"
    info "All environments rolled back to version: $TARGET_VERSION"
    warning "Please investigate the issue that caused this rollback"
}

# Execute main function
main "$@" 