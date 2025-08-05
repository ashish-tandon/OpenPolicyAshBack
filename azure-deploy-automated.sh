#!/bin/bash

# 🚀 Automated Azure Deployment Script
# This script follows the standardized deployment process

set -e

# Configuration
RESOURCE_GROUP="openpolicy-rg"
LOCATION="eastus"
ACR_NAME="openpolicyacr"
CONTAINER_APP_NAME="openpolicy-api"
ENVIRONMENT_NAME="openpolicy-env"
BASE_URL="https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io"

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

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        error "Azure CLI is not installed. Please install it first: brew install azure-cli"
        exit 1
    fi
    success "Azure CLI is installed"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install it first: https://docs.docker.com/get-docker/"
        exit 1
    fi
    success "Docker is installed"
    
    # Check Azure login
    if ! az account show &> /dev/null; then
        warning "Not logged in to Azure. Please login..."
        az login
    fi
    success "Logged in to Azure"
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running. Please start Docker Desktop"
        exit 1
    fi
    success "Docker daemon is running"
}

# Function to register providers
register_providers() {
    log "Registering Azure providers..."
    
    local providers=("Microsoft.ContainerRegistry" "Microsoft.ContainerInstance" "Microsoft.App" "Microsoft.OperationalInsights")
    
    for provider in "${providers[@]}"; do
        log "Registering $provider..."
        az provider register --namespace "$provider" --wait
        success "$provider registered"
    done
}

# Function to create infrastructure
create_infrastructure() {
    log "Creating infrastructure..."
    
    # Create resource group
    if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
        log "Creating resource group: $RESOURCE_GROUP"
        az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
        success "Resource group created"
    else
        warning "Resource group $RESOURCE_GROUP already exists"
    fi
    
    # Create container registry
    if ! az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log "Creating container registry: $ACR_NAME"
        az acr create --resource-group "$RESOURCE_GROUP" --name "$ACR_NAME" --sku Basic
        success "Container registry created"
    else
        warning "Container registry $ACR_NAME already exists"
    fi
    
    # Enable admin access
    log "Enabling admin access to ACR..."
    az acr update -n "$ACR_NAME" --admin-enabled true
    success "Admin access enabled"
    
    # Get ACR credentials
    log "Getting ACR credentials..."
    ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" --output tsv)
    success "ACR credentials retrieved"
    
    # Create Container Apps environment
    if ! az containerapp env show --name "$ENVIRONMENT_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        log "Creating Container Apps environment: $ENVIRONMENT_NAME"
        az containerapp env create --name "$ENVIRONMENT_NAME" --resource-group "$RESOURCE_GROUP" --location "$LOCATION" --logs-destination none
        success "Container Apps environment created"
    else
        warning "Container Apps environment $ENVIRONMENT_NAME already exists"
    fi
}

# Function to fix code issues
fix_code_issues() {
    log "Fixing code issues..."
    
    # Fix import issues in main.py
    log "Fixing imports in main.py..."
    sed -i '' 's/from api\./from src.api./g' src/api/main.py
    sed -i '' 's/from api\./from src.api./g' src/api/progress_api.py
    
    # Fix relative imports in progress_api.py
    log "Fixing relative imports in progress_api.py..."
    sed -i '' 's/from \.\.progress_tracker/from src.progress_tracker/g' src/api/progress_api.py
    sed -i '' 's/from \.\.database/from src.database/g' src/api/progress_api.py
    sed -i '' 's/from \.\.scrapers/from src.scrapers/g' src/api/progress_api.py
    
    # Fix ScraperManager initialization
    log "Fixing ScraperManager initialization..."
    sed -i '' 's/ScraperManager(self\.session_factory())/ScraperManager()/g' src/phased_loading.py
    
    # Create missing __init__.py files
    log "Creating __init__.py files..."
    touch src/api/__init__.py
    
    success "Code issues fixed"
}

# Function to build and push Docker image
build_and_push() {
    log "Building and pushing Docker image..."
    
    # Login to ACR
    log "Logging in to ACR..."
    az acr login --name "$ACR_NAME"
    success "Logged in to ACR"
    
    # Build image
    log "Building Docker image..."
    docker build --platform linux/amd64 -f Dockerfile.api-simple -t "$ACR_NAME.azurecr.io/openpolicy-api:latest" .
    success "Docker image built"
    
    # Push image
    log "Pushing image to registry..."
    docker push "$ACR_NAME.azurecr.io/openpolicy-api:latest"
    success "Image pushed to registry"
}

# Function to deploy container app
deploy_container_app() {
    log "Deploying container app..."
    
    # Check if container app exists
    if az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        warning "Container app $CONTAINER_APP_NAME already exists. Updating..."
        
        # Update container app
        az containerapp update \
            --name "$CONTAINER_APP_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --image "$ACR_NAME.azurecr.io/openpolicy-api:latest"
        
        success "Container app updated"
    else
        # Create new container app
        log "Creating new container app..."
        az containerapp create \
            --name "$CONTAINER_APP_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --environment "$ENVIRONMENT_NAME" \
            --image "$ACR_NAME.azurecr.io/openpolicy-api:latest" \
            --registry-server "$ACR_NAME.azurecr.io" \
            --registry-username "$ACR_NAME" \
            --registry-password "$ACR_PASSWORD" \
            --target-port 8000 \
            --ingress external \
            --env-vars \
                DATABASE_URL="sqlite:///./openpolicy.db" \
                REDIS_URL="redis://localhost:6379/0" \
                CORS_ORIGINS="https://$CONTAINER_APP_NAME.azurecontainerapps.io" \
                NODE_ENV="production" \
            --cpu 1 \
            --memory 2Gi \
            --min-replicas 1 \
            --max-replicas 3
        
        success "Container app created"
    fi
}

# Function to monitor deployment
monitor_deployment() {
    log "Monitoring deployment..."
    
    # Wait for container to start
    log "Waiting for container to start..."
    sleep 30
    
    # Get container status
    local status=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.runningStatus" --output tsv)
    local fqdn=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.configuration.ingress.fqdn" --output tsv)
    
    echo "📊 Container Status: $status"
    echo "🌐 FQDN: $fqdn"
    
    if [ "$status" = "Running" ]; then
        success "Container is running"
        
        # Test health endpoint
        log "Testing health endpoint..."
        sleep 30
        
        if curl -f -s --max-time 30 "https://$fqdn/health" >/dev/null 2>&1; then
            success "Health endpoint is responding"
        else
            warning "Health endpoint is not responding yet (checking logs...)"
            
            # Show recent logs
            log "Recent logs:"
            az containerapp logs show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --tail 20
        fi
    else
        error "Container is not running (Status: $status)"
        
        # Show logs for debugging
        log "Container logs:"
        az containerapp logs show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --tail 50
    fi
}

# Function to run verification
run_verification() {
    log "Running deployment verification..."
    
    if [ -f "./deployment-verification.sh" ]; then
        ./deployment-verification.sh
    else
        warning "deployment-verification.sh not found, running basic tests..."
        
        local fqdn=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.configuration.ingress.fqdn" --output tsv)
        
        # Basic endpoint tests
        curl -f -s --max-time 30 "https://$fqdn/health" >/dev/null 2>&1 && success "Health endpoint: OK" || error "Health endpoint: FAILED"
        curl -f -s --max-time 30 "https://$fqdn/docs" >/dev/null 2>&1 && success "API docs: OK" || error "API docs: FAILED"
        curl -f -s --max-time 30 "https://$fqdn/stats" >/dev/null 2>&1 && success "Stats endpoint: OK" || error "Stats endpoint: FAILED"
    fi
}

# Function to show live monitoring commands
show_monitoring_commands() {
    echo ""
    echo "🔍 Live Monitoring Commands:"
    echo ""
    echo "   # Real-time logs"
    echo "   az containerapp logs show --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME --follow"
    echo ""
    echo "   # Check status"
    echo "   az containerapp show --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME --query 'properties.runningStatus'"
    echo ""
    echo "   # Test health endpoint"
    echo "   curl -f https://$BASE_URL/health"
    echo ""
    echo "   # Run full verification"
    echo "   ./deployment-verification.sh"
    echo ""
}

# Function to create deployment summary
create_deployment_summary() {
    local timestamp=$(date +'%Y-%m-%d_%H-%M-%S')
    local summary_file="azure_deployment_summary_${timestamp}.md"
    local fqdn=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.configuration.ingress.fqdn" --output tsv 2>/dev/null || echo "Unknown")
    local revision=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.latestReadyRevisionName" --output tsv 2>/dev/null || echo "Unknown")
    
    cat > "$summary_file" << EOF
# Azure Deployment Summary

**Deployment Date:** $(date +'%Y-%m-%d %H:%M:%S')
**Resource Group:** $RESOURCE_GROUP
**Location:** $LOCATION
**Container App:** $CONTAINER_APP_NAME
**Environment:** $ENVIRONMENT_NAME

## Container Information
- **FQDN:** $fqdn
- **Revision:** $revision
- **Status:** Running

## Access URLs
- **Main API:** https://$fqdn
- **Health Check:** https://$fqdn/health
- **API Documentation:** https://$fqdn/docs
- **Stats:** https://$fqdn/stats

## Live Monitoring Commands
\`\`\`bash
# Real-time logs
az containerapp logs show --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME --follow

# Check status
az containerapp show --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME --query 'properties.runningStatus'

# Test health endpoint
curl -f https://$fqdn/health

# Run full verification
./deployment-verification.sh
\`\`\`

## Management Commands
\`\`\`bash
# Update container app
az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --image $ACR_NAME.azurecr.io/openpolicy-api:latest

# Restart container app
az containerapp restart --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP

# Delete container app
az containerapp delete --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --yes
\`\`\`

EOF

    success "Deployment summary created: $summary_file"
}

# Main function
main() {
    echo "🚀 Starting automated Azure deployment..."
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Location: $LOCATION"
    echo "Container Registry: $ACR_NAME"
    echo "Container App: $CONTAINER_APP_NAME"
    echo "Environment: $ENVIRONMENT_NAME"
    echo ""
    
    # Run all steps
    check_prerequisites
    register_providers
    create_infrastructure
    fix_code_issues
    build_and_push
    deploy_container_app
    monitor_deployment
    run_verification
    show_monitoring_commands
    create_deployment_summary
    
    echo ""
    success "Automated deployment completed!"
    echo "🎉 Your OpenPolicy application is now running on Azure!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Use the live monitoring commands above to check the deployment"
    echo "   2. Test all endpoints using the verification script"
    echo "   3. Monitor logs for any issues"
    echo "   4. Update the deployment summary with any issues found"
}

# Run main function
main "$@" 