#!/bin/bash

# 🚀 Azure Container Apps Deployment Script for OpenPolicy
# This script deploys OpenPolicy to Azure Container Apps (recommended for production)

set -e

# Configuration - Update these values
RESOURCE_GROUP="openpolicy-rg"
LOCATION="eastus"
ACR_NAME="openpolicyacr"
CONTAINER_APP_NAME="openpolicy-app"
ENVIRONMENT_NAME="openpolicy-env"

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

# Function to register Container Apps provider
register_container_apps() {
    log "Registering Container Apps provider..."
    
    # Register the Container Apps provider
    az provider register --namespace Microsoft.App
    
    # Wait for registration to complete
    log "Waiting for provider registration to complete..."
    while [ "$(az provider show --namespace Microsoft.App --query registrationState --output tsv)" != "Registered" ]; do
        echo "   Waiting for Microsoft.App provider registration..."
        sleep 10
    done
    success "Container Apps provider registered"
}

# Function to create Container Apps environment
create_environment() {
    log "Creating Container Apps environment: $ENVIRONMENT_NAME"
    
    if az containerapp env show --name "$ENVIRONMENT_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        warning "Container Apps environment $ENVIRONMENT_NAME already exists"
    else
        az containerapp env create \
            --name "$ENVIRONMENT_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --location "$LOCATION"
        success "Container Apps environment created"
    fi
}

# Function to deploy Container App
deploy_container_app() {
    log "Deploying Container App: $CONTAINER_APP_NAME"
    
    # Check if container app already exists
    if az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        warning "Container App $CONTAINER_APP_NAME already exists. Updating..."
        
        # Update the container app
        az containerapp update \
            --name "$CONTAINER_APP_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --image "$ACR_NAME.azurecr.io/openpolicy:latest" \
            --set-env-vars \
                DATABASE_URL="postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata" \
                REDIS_URL="redis://localhost:6379/0" \
                CORS_ORIGINS="https://$CONTAINER_APP_NAME.azurecontainerapps.io" \
                NODE_ENV="production"
    else
        # Create new container app
        az containerapp create \
            --name "$CONTAINER_APP_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --environment "$ENVIRONMENT_NAME" \
            --image "$ACR_NAME.azurecr.io/openpolicy:latest" \
            --target-port 80 \
            --ingress external \
            --env-vars \
                DATABASE_URL="postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata" \
                REDIS_URL="redis://localhost:6379/0" \
                CORS_ORIGINS="https://$CONTAINER_APP_NAME.azurecontainerapps.io" \
                NODE_ENV="production" \
            --cpu 2 \
            --memory 4Gi \
            --min-replicas 1 \
            --max-replicas 3
    fi
    
    success "Container App deployed successfully"
}

# Function to get Container App information
get_container_app_info() {
    log "Getting Container App information..."
    
    # Get the FQDN
    local fqdn=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.configuration.ingress.fqdn" --output tsv)
    
    # Get the revision name
    local revision=$(az containerapp revision list --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "[0].name" --output tsv)
    
    echo ""
    echo "🎉 Container Apps deployment completed successfully!"
    echo ""
    echo "📊 Container App Information:"
    echo "   Resource Group: $RESOURCE_GROUP"
    echo "   Container App Name: $CONTAINER_APP_NAME"
    echo "   Environment: $ENVIRONMENT_NAME"
    echo "   FQDN: $fqdn"
    echo "   Revision: $revision"
    echo ""
    echo "🌐 Access URLs:"
    echo "   Main Dashboard: https://$fqdn"
    echo "   API Documentation: https://$fqdn:8000/docs"
    echo "   Health Check: https://$fqdn:8000/health"
    echo "   Flower Monitor: https://$fqdn:5555"
    echo "   Direct API: https://$fqdn:8000"
    echo "   Direct Dashboard: https://$fqdn:3000"
    echo ""
}

# Function to test the deployment
test_deployment() {
    log "Testing deployment..."
    
    # Wait a bit for services to start
    sleep 30
    
    # Get the FQDN
    local fqdn=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.configuration.ingress.fqdn" --output tsv)
    
    # Test health endpoint
    log "Testing health endpoint..."
    if curl -f -s --max-time 30 "https://$fqdn:8000/health" >/dev/null 2>&1; then
        success "Health endpoint is responding"
    else
        warning "Health endpoint is not responding yet (this is normal during startup)"
    fi
    
    # Test main dashboard
    log "Testing main dashboard..."
    if curl -f -s --max-time 30 "https://$fqdn" >/dev/null 2>&1; then
        success "Main dashboard is responding"
    else
        warning "Main dashboard is not responding yet (this is normal during startup)"
    fi
    
    echo ""
    echo "💡 Note: It may take 2-3 minutes for all services to fully start up."
    echo "   You can check the status using: az containerapp logs show --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME"
}

# Function to show management commands
show_management_commands() {
    echo ""
    echo "🔧 Management Commands:"
    echo ""
    echo "   # View container app logs"
    echo "   az containerapp logs show --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME"
    echo ""
    echo "   # Check container app status"
    echo "   az containerapp show --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME"
    echo ""
    echo "   # Scale container app"
    echo "   az containerapp revision set-mode --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --mode multiple"
    echo ""
    echo "   # Update container app"
    echo "   az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --image $ACR_NAME.azurecr.io/openpolicy:latest"
    echo ""
    echo "   # Delete container app"
    echo "   az containerapp delete --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --yes"
    echo ""
    echo "   # Delete resource group (removes everything)"
    echo "   az group delete --name $RESOURCE_GROUP --yes"
    echo ""
}

# Function to create deployment summary
create_deployment_summary() {
    local timestamp=$(date +'%Y-%m-%d_%H-%M-%S')
    local summary_file="azure_container_apps_summary_${timestamp}.md"
    
    local fqdn=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.configuration.ingress.fqdn" --output tsv)
    local revision=$(az containerapp revision list --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "[0].name" --output tsv)
    
    cat > "$summary_file" << EOF
# Azure Container Apps Deployment Summary

**Deployment Date:** $(date +'%Y-%m-%d %H:%M:%S')
**Resource Group:** $RESOURCE_GROUP
**Location:** $LOCATION
**Container App Name:** $CONTAINER_APP_NAME
**Environment:** $ENVIRONMENT_NAME

## Container App Information

- **FQDN:** $fqdn
- **Revision:** $revision
- **Status:** Running

## Access URLs

- **Main Dashboard:** https://$fqdn
- **API Documentation:** https://$fqdn:8000/docs
- **Health Check:** https://$fqdn:8000/health
- **Flower Monitor:** https://$fqdn:5555
- **Direct API:** https://$fqdn:8000
- **Direct Dashboard:** https://$fqdn:3000

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
az containerapp logs show --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME

# Check status
az containerapp show --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME

# Scale app
az containerapp revision set-mode --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --mode multiple

# Update app
az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --image $ACR_NAME.azurecr.io/openpolicy:latest
\`\`\`

## Next Steps

1. Monitor the system for 24 hours
2. Test all API endpoints
3. Verify data scraping is working
4. Set up monitoring and alerts
5. Configure auto-scaling rules
6. Set up custom domain if needed

EOF

    success "Deployment summary created: $summary_file"
}

# Main function
main() {
    echo "🚀 Starting Azure Container Apps deployment for OpenPolicy"
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Location: $LOCATION"
    echo "Container Registry: $ACR_NAME"
    echo "Container App Name: $CONTAINER_APP_NAME"
    echo "Environment: $ENVIRONMENT_NAME"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Create resource group
    create_resource_group
    
    # Create container registry
    create_container_registry
    
    # Build and push image
    build_and_push_image
    
    # Register Container Apps provider
    register_container_apps
    
    # Create Container Apps environment
    create_environment
    
    # Deploy Container App
    deploy_container_app
    
    # Get Container App information
    get_container_app_info
    
    # Test deployment
    test_deployment
    
    # Show management commands
    show_management_commands
    
    # Create deployment summary
    create_deployment_summary
    
    echo ""
    success "Azure Container Apps deployment completed successfully!"
    echo "🎉 Your OpenPolicy application is now running on Azure Container Apps!"
}

# Run main function
main "$@" 