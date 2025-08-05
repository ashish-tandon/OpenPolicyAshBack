#!/bin/bash

# 🚀 Azure Deployment Script for OpenPolicy
# This script automates the deployment of OpenPolicy to Azure Container Instances

set -e

# Configuration - Update these values
RESOURCE_GROUP="openpolicy-rg"
LOCATION="eastus"
ACR_NAME="openpolicyacr"
CONTAINER_NAME="openpolicy-container"
SUBSCRIPTION_ID=""  # Leave empty to use default

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
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        error "Azure CLI is not installed. Please install it first: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
    success "Azure CLI is installed"
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install it first: https://docs.docker.com/get-docker/"
        exit 1
    fi
    success "Docker is installed"
    
    # Check if user is logged in to Azure
    if ! az account show &> /dev/null; then
        warning "Not logged in to Azure. Please login..."
        az login
    fi
    success "Logged in to Azure"
    
    # Set subscription if provided
    if [ ! -z "$SUBSCRIPTION_ID" ]; then
        log "Setting subscription to: $SUBSCRIPTION_ID"
        az account set --subscription "$SUBSCRIPTION_ID"
        success "Subscription set"
    fi
}

# Function to create resource group
create_resource_group() {
    log "Creating resource group: $RESOURCE_GROUP"
    
    if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
        warning "Resource group $RESOURCE_GROUP already exists"
    else
        az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
        success "Resource group created"
    fi
}

# Function to create container registry
create_container_registry() {
    log "Creating container registry: $ACR_NAME"
    
    if az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        warning "Container registry $ACR_NAME already exists"
    else
        az acr create --resource-group "$RESOURCE_GROUP" --name "$ACR_NAME" --sku Basic
        success "Container registry created"
    fi
    
    # Login to ACR
    log "Logging in to container registry..."
    az acr login --name "$ACR_NAME"
    success "Logged in to container registry"
}

# Function to build and push Docker image
build_and_push_image() {
    log "Building Docker image..."
    
    # Check if Dockerfile exists
    if [ ! -f "Dockerfile.single-container" ]; then
        error "Dockerfile.single-container not found in current directory"
        exit 1
    fi
    
    # Build the image
    docker build -f Dockerfile.single-container -t "$ACR_NAME.azurecr.io/openpolicy:latest" .
    success "Docker image built"
    
    # Push to registry
    log "Pushing image to container registry..."
    docker push "$ACR_NAME.azurecr.io/openpolicy:latest"
    success "Image pushed to registry"
}

# Function to deploy container
deploy_container() {
    log "Deploying container to Azure Container Instances..."
    
    # Check if container already exists
    if az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" &> /dev/null; then
        warning "Container $CONTAINER_NAME already exists. Updating..."
        az container delete --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --yes
        log "Waiting for container deletion..."
        sleep 30
    fi
    
    # Deploy the container
    az container create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$CONTAINER_NAME" \
        --image "$ACR_NAME.azurecr.io/openpolicy:latest" \
        --dns-name-label "openpolicy-app" \
        --ports 80 8000 3000 5555 \
        --environment-variables \
            DATABASE_URL="postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata" \
            REDIS_URL="redis://localhost:6379/0" \
            CORS_ORIGINS="https://openpolicy-app.eastus.azurecontainer.io,http://localhost:3000" \
            NODE_ENV="production" \
        --memory 4 \
        --cpu 2 \
        --restart-policy Always
    
    success "Container deployed successfully"
}

# Function to wait for container to be ready
wait_for_container() {
    log "Waiting for container to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --query "provisioningState" --output tsv | grep -q "Succeeded"; then
            success "Container is ready"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - Container not ready yet..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    error "Container failed to become ready after $max_attempts attempts"
    return 1
}

# Function to get container information
get_container_info() {
    log "Getting container information..."
    
    # Get the public IP
    local ip_address=$(az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --query "ipAddress.ip" --output tsv)
    
    # Get the FQDN
    local fqdn=$(az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --query "ipAddress.fqdn" --output tsv)
    
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "📊 Container Information:"
    echo "   Resource Group: $RESOURCE_GROUP"
    echo "   Container Name: $CONTAINER_NAME"
    echo "   IP Address: $ip_address"
    echo "   FQDN: $fqdn"
    echo ""
    echo "🌐 Access URLs:"
    echo "   Main Dashboard: http://$fqdn"
    echo "   API Documentation: http://$fqdn:8000/docs"
    echo "   Health Check: http://$fqdn:8000/health"
    echo "   Flower Monitor: http://$fqdn:5555"
    echo "   Direct API: http://$fqdn:8000"
    echo "   Direct Dashboard: http://$fqdn:3000"
    echo ""
}

# Function to test the deployment
test_deployment() {
    log "Testing deployment..."
    
    # Wait a bit for services to start
    sleep 30
    
    # Get the FQDN
    local fqdn=$(az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --query "ipAddress.fqdn" --output tsv)
    
    # Test health endpoint
    log "Testing health endpoint..."
    if curl -f -s --max-time 30 "http://$fqdn:8000/health" >/dev/null 2>&1; then
        success "Health endpoint is responding"
    else
        warning "Health endpoint is not responding yet (this is normal during startup)"
    fi
    
    # Test main dashboard
    log "Testing main dashboard..."
    if curl -f -s --max-time 30 "http://$fqdn" >/dev/null 2>&1; then
        success "Main dashboard is responding"
    else
        warning "Main dashboard is not responding yet (this is normal during startup)"
    fi
    
    echo ""
    echo "💡 Note: It may take 2-3 minutes for all services to fully start up."
    echo "   You can check the status using: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
}

# Function to show management commands
show_management_commands() {
    echo ""
    echo "🔧 Management Commands:"
    echo ""
    echo "   # View container logs"
    echo "   az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
    echo ""
    echo "   # Check container status"
    echo "   az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
    echo ""
    echo "   # Stop container"
    echo "   az container stop --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
    echo ""
    echo "   # Start container"
    echo "   az container start --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
    echo ""
    echo "   # Delete container"
    echo "   az container delete --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --yes"
    echo ""
    echo "   # Delete resource group (removes everything)"
    echo "   az group delete --name $RESOURCE_GROUP --yes"
    echo ""
}

# Function to create deployment summary
create_deployment_summary() {
    local timestamp=$(date +'%Y-%m-%d_%H-%M-%S')
    local summary_file="azure_deployment_summary_${timestamp}.md"
    
    local fqdn=$(az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --query "ipAddress.fqdn" --output tsv)
    local ip_address=$(az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --query "ipAddress.ip" --output tsv)
    
    cat > "$summary_file" << EOF
# Azure Deployment Summary

**Deployment Date:** $(date +'%Y-%m-%d %H:%M:%S')
**Resource Group:** $RESOURCE_GROUP
**Location:** $LOCATION
**Container Name:** $CONTAINER_NAME

## Container Information

- **IP Address:** $ip_address
- **FQDN:** $fqdn
- **Status:** Running

## Access URLs

- **Main Dashboard:** http://$fqdn
- **API Documentation:** http://$fqdn:8000/docs
- **Health Check:** http://$fqdn:8000/health
- **Flower Monitor:** http://$fqdn:5555
- **Direct API:** http://$fqdn:8000
- **Direct Dashboard:** http://$fqdn:3000

## Services Included

1. **PostgreSQL Database** - Port 5432
2. **Redis Cache** - Port 6379
3. **FastAPI Backend** - Port 8000
4. **React Dashboard** - Port 3000
5. **Celery Worker** - Background
6. **Celery Beat** - Background
7. **Flower Monitor** - Port 5555
8. **Nginx Reverse Proxy** - Port 80

## Management Commands

\`\`\`bash
# View logs
az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME

# Check status
az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME

# Stop container
az container stop --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME

# Start container
az container start --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME
\`\`\`

## Next Steps

1. Monitor the system for 24 hours
2. Test all API endpoints
3. Verify data scraping is working
4. Set up monitoring and alerts
5. Configure backups if needed

EOF

    success "Deployment summary created: $summary_file"
}

# Main function
main() {
    echo "🚀 Starting Azure deployment for OpenPolicy"
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Location: $LOCATION"
    echo "Container Registry: $ACR_NAME"
    echo "Container Name: $CONTAINER_NAME"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Create resource group
    create_resource_group
    
    # Create container registry
    create_container_registry
    
    # Build and push image
    build_and_push_image
    
    # Deploy container
    deploy_container
    
    # Wait for container to be ready
    wait_for_container
    
    # Get container information
    get_container_info
    
    # Test deployment
    test_deployment
    
    # Show management commands
    show_management_commands
    
    # Create deployment summary
    create_deployment_summary
    
    echo ""
    success "Azure deployment completed successfully!"
    echo "🎉 Your OpenPolicy application is now running on Azure!"
}

# Run main function
main "$@" 