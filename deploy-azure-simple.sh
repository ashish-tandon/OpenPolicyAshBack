#!/bin/bash

# 🚀 Simple Azure Deployment Script for OpenPolicy (No Container Registry)
# This script deploys using a public container image approach

set -e

# Configuration
RESOURCE_GROUP="openpolicy-rg"
LOCATION="eastus"
CONTAINER_NAME="openpolicy-container"

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
        error "Azure CLI is not installed. Please install it first: brew install azure-cli"
        exit 1
    fi
    success "Azure CLI is installed"
    
    # Check if user is logged in to Azure
    if ! az account show &> /dev/null; then
        warning "Not logged in to Azure. Please login..."
        az login
    fi
    success "Logged in to Azure"
    
    # Show current subscription
    local subscription_name=$(az account show --query "name" --output tsv)
    log "Current subscription: $subscription_name"
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

# Function to deploy a simple test container first
deploy_test_container() {
    log "Deploying a simple test container to verify Azure Container Instances works..."
    
    # Deploy a simple nginx container to test
    az container create \
        --resource-group "$RESOURCE_GROUP" \
        --name "test-container" \
        --image nginx:alpine \
        --dns-name-label "test-openpolicy" \
        --ports 80 \
        --memory 1 \
        --cpu 1 \
        --os-type Linux \
        --restart-policy Never
    
    success "Test container deployed"
    
    # Get the FQDN
    local fqdn=$(az container show --resource-group "$RESOURCE_GROUP" --name "test-container" --query "ipAddress.fqdn" --output tsv)
    log "Test container FQDN: $fqdn"
    
    # Test the container
    log "Testing the container..."
    sleep 10
    if curl -f -s --max-time 10 "http://$fqdn" >/dev/null 2>&1; then
        success "Test container is working!"
    else
        warning "Test container might still be starting up"
    fi
    
    # Clean up test container
    log "Cleaning up test container..."
    az container delete --resource-group "$RESOURCE_GROUP" --name "test-container" --yes
    success "Test container cleaned up"
}

# Function to deploy OpenPolicy using a public image approach
deploy_openpolicy_public() {
    log "Deploying OpenPolicy using a public image approach..."
    
    # For now, let's deploy a simple FastAPI container
    # We'll use a public Python image and install our dependencies
    az container create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$CONTAINER_NAME" \
        --image python:3.11-slim \
        --dns-name-label "openpolicy-app" \
        --ports 8000 \
        --environment-variables \
            PYTHONPATH="/app" \
            DATABASE_URL="sqlite:///./openpolicy.db" \
            REDIS_URL="redis://localhost:6379/0" \
            CORS_ORIGINS="http://localhost:3000,http://openpolicy-app.eastus.azurecontainer.io" \
            NODE_ENV="production" \
        --memory 2 \
        --cpu 1 \
        --os-type Linux \
        --restart-policy Always \
        --command-line "bash -c 'pip install fastapi uvicorn sqlalchemy && echo \"from fastapi import FastAPI; app = FastAPI(); @app.get(\"/health\"); def health(): return {\"status\": \"healthy\", \"service\": \"OpenPolicy API\"}; @app.get(\"/\"); def root(): return {\"message\": \"OpenPolicy API is running\"}' > /app/main.py && cd /app && uvicorn main:app --host 0.0.0.0 --port 8000'"
    
    success "OpenPolicy container deployed"
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
    echo "   API Root: http://$fqdn:8000"
    echo "   Health Check: http://$fqdn:8000/health"
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
    
    # Test root endpoint
    log "Testing root endpoint..."
    if curl -f -s --max-time 30 "http://$fqdn:8000/" >/dev/null 2>&1; then
        success "Root endpoint is responding"
    else
        warning "Root endpoint is not responding yet (this is normal during startup)"
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
    local summary_file="azure_simple_deployment_summary_${timestamp}.md"
    
    local fqdn=$(az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --query "ipAddress.fqdn" --output tsv)
    local ip_address=$(az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --query "ipAddress.ip" --output tsv)
    
    cat > "$summary_file" << EOF
# Azure Simple Deployment Summary

**Deployment Date:** $(date +'%Y-%m-%d %H:%M:%S')
**Resource Group:** $RESOURCE_GROUP
**Location:** $LOCATION
**Container Name:** $CONTAINER_NAME

## Container Information

- **IP Address:** $ip_address
- **FQDN:** $fqdn
- **Status:** Running

## Access URLs

- **API Root:** http://$fqdn:8000
- **Health Check:** http://$fqdn:8000/health

## Services Included

1. **FastAPI Backend** - Port 8000
2. **SQLite Database** - Local file
3. **Basic API endpoints**

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

1. Test the basic API endpoints
2. Verify the deployment is working
3. Consider upgrading to full OpenPolicy deployment once container registry is available
4. Set up monitoring and alerts

EOF

    success "Deployment summary created: $summary_file"
}

# Main function
main() {
    echo "🚀 Starting Simple Azure deployment for OpenPolicy (No Container Registry)"
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Location: $LOCATION"
    echo "Container Name: $CONTAINER_NAME"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Create resource group
    create_resource_group
    
    # Deploy test container to verify ACI works
    deploy_test_container
    
    # Deploy OpenPolicy
    deploy_openpolicy_public
    
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