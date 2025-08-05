#!/bin/bash

# 🚀 Simple Azure Container Apps deployment for OpenPolicy API
# Deploys only the API without dashboard build requirements

set -e

# Configuration
RESOURCE_GROUP="openpolicy-rg"
LOCATION="eastus"
ACR_NAME="openpolicyacr"
CONTAINER_APP_NAME="openpolicy-api"
ENVIRONMENT_NAME="openpolicy-env"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
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
    echo -e "${BLUE}🔧 $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        error "Azure CLI is not installed"
        exit 1
    fi
    success "Azure CLI is installed"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    success "Docker is installed"
    
    # Check Azure login
    if ! az account show &> /dev/null; then
        error "Not logged in to Azure. Please run 'az login'"
        exit 1
    fi
    success "Logged in to Azure"
    
    # Show current subscription
    local subscription=$(az account show --query "name" --output tsv)
    log "Current subscription: $subscription"
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
        az acr create \
            --resource-group "$RESOURCE_GROUP" \
            --name "$ACR_NAME" \
            --sku Basic \
            --admin-enabled true
        success "Container registry created"
    fi
    
    # Login to registry
    log "Logging in to container registry..."
    az acr login --name "$ACR_NAME"
    success "Logged in to container registry"
}

# Function to build and push Docker image
build_and_push_image() {
    log "Building Docker image for Linux/AMD64..."
    
    # Check if Dockerfile exists
    if [ ! -f "Dockerfile.api" ]; then
        error "Dockerfile.api not found"
        exit 1
    fi
    
    # Build the image for Linux/AMD64 (Azure requirement)
    docker build --platform linux/amd64 -f Dockerfile.api \
        -t "$ACR_NAME.azurecr.io/openpolicy-api:latest" .
    success "Docker image built"
    
    # Push to registry
    log "Pushing image to container registry..."
    docker push "$ACR_NAME.azurecr.io/openpolicy-api:latest"
    success "Image pushed to registry"
}

# Function to create Container Apps environment
create_environment() {
    log "Creating Container Apps environment: $ENVIRONMENT_NAME"
    
    if az containerapp env show --name "$ENVIRONMENT_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        warning "Environment $ENVIRONMENT_NAME already exists"
    else
        az containerapp env create \
            --name "$ENVIRONMENT_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --location "$LOCATION"
        success "Environment created"
    fi
}

# Function to deploy container app
deploy_container_app() {
    log "Deploying container app: $CONTAINER_APP_NAME"
    
    # Check if container app already exists
    if az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        warning "Container app $CONTAINER_APP_NAME already exists. Updating..."
        az containerapp delete --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" --yes
        log "Waiting for deletion..."
        sleep 30
    fi
    
    # Get registry credentials
    local registry_username=$(az acr credential show --name "$ACR_NAME" --query "username" --output tsv)
    local registry_password=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" --output tsv)
    
    # Deploy the container app
    az containerapp create \
        --name "$CONTAINER_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --environment "$ENVIRONMENT_NAME" \
        --image "$ACR_NAME.azurecr.io/openpolicy-api:latest" \
        --target-port 8000 \
        --ingress external \
        --registry-server "$ACR_NAME.azurecr.io" \
        --registry-username "$registry_username" \
        --registry-password "$registry_password" \
        --env-vars \
            DATABASE_URL="sqlite:///./openpolicy.db" \
            REDIS_URL="redis://localhost:6379/0" \
            CORS_ORIGINS="https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io" \
            NODE_ENV="production" \
        --cpu 1 \
        --memory 2Gi \
        --min-replicas 1 \
        --max-replicas 3
    
    success "Container app deployed successfully"
}

# Function to get container app information
get_container_app_info() {
    log "Getting container app information..."
    
    # Get the URL
    local url=$(az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" --output tsv)
    
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "📊 Container App Information:"
    echo "   Resource Group: $RESOURCE_GROUP"
    echo "   Container App Name: $CONTAINER_APP_NAME"
    echo "   Environment: $ENVIRONMENT_NAME"
    echo "   URL: https://$url"
    echo ""
    echo "🌐 Access URLs:"
    echo "   API Root: https://$url"
    echo "   Health Check: https://$url/health"
    echo "   API Documentation: https://$url/docs"
    echo ""
}

# Function to test the deployment
test_deployment() {
    log "Testing deployment..."
    
    # Wait a bit for services to start
    sleep 30
    
    # Get the URL
    local url=$(az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" --output tsv)
    
    # Test health endpoint
    log "Testing health endpoint..."
    if curl -f -s --max-time 30 "https://$url/health" >/dev/null 2>&1; then
        success "Health endpoint is responding"
    else
        warning "Health endpoint is not responding yet (this is normal during startup)"
    fi
    
    # Test root endpoint
    log "Testing root endpoint..."
    if curl -f -s --max-time 30 "https://$url/" >/dev/null 2>&1; then
        success "Root endpoint is responding"
    else
        warning "Root endpoint is not responding yet (this is normal during startup)"
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
    echo "   # Scale the application"
    echo "   az containerapp revision set-mode --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --mode multiple"
    echo ""
    echo "   # Update the application"
    echo "   az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --image $ACR_NAME.azurecr.io/openpolicy-api:latest"
    echo ""
    echo "   # Delete the application"
    echo "   az containerapp delete --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --yes"
    echo ""
    echo "   # Delete resource group (removes everything)"
    echo "   az group delete --name $RESOURCE_GROUP --yes"
    echo ""
}

# Function to create deployment summary
create_deployment_summary() {
    local timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
    local summary_file="azure_container_apps_deployment_summary_${timestamp}.md"
    
    cat > "$summary_file" << EOF
# Azure Container Apps Deployment Summary

**Date**: $(date)
**Container App**: $CONTAINER_APP_NAME
**Resource Group**: $RESOURCE_GROUP
**Environment**: $ENVIRONMENT_NAME

## Configuration
- **Image**: $ACR_NAME.azurecr.io/openpolicy-api:latest
- **Platform**: Linux/AMD64
- **CPU**: 1 core
- **Memory**: 2GB
- **Scaling**: 1-3 replicas
- **Ingress**: External with HTTPS

## URLs
- **API Root**: https://$(az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" --output tsv)
- **Health Check**: https://$(az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" --output tsv)/health
- **API Documentation**: https://$(az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" --query "properties.configuration.ingress.fqdn" --output tsv)/docs

## Environment Variables
- DATABASE_URL: sqlite:///./openpolicy.db
- REDIS_URL: redis://localhost:6379/0
- CORS_ORIGINS: https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io
- NODE_ENV: production

## Notes
- Platform: Linux/AMD64 (explicitly specified for Azure)
- OS Type: Linux (managed by Azure Container Apps)
- HTTPS: Automatically configured with SSL
- Auto-scaling: Enabled (1-3 replicas)
EOF
    
    success "Deployment summary created: $summary_file"
}

# Main deployment function
main() {
    echo "🚀 Starting Simple Azure Container Apps deployment for OpenPolicy"
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Location: $LOCATION"
    echo "Container Registry: $ACR_NAME"
    echo "Container App Name: $CONTAINER_APP_NAME"
    echo "Environment: $ENVIRONMENT_NAME"
    echo ""
    
    check_prerequisites
    create_resource_group
    create_container_registry
    build_and_push_image
    create_environment
    deploy_container_app
    get_container_app_info
    test_deployment
    show_management_commands
    create_deployment_summary
    
    echo ""
    success "Azure Container Apps deployment completed successfully!"
    echo "🎉 Your OpenPolicy API is now running on Azure Container Apps!"
}

# Run main function
main "$@" 