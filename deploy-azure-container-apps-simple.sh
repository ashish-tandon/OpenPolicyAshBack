#!/bin/bash

# 🚀 Azure Container Apps Deployment Script for OpenPolicy API (Simple)
# This script deploys just the API to Azure Container Apps

set -e

# Configuration
RESOURCE_GROUP="openpolicy-rg"
LOCATION="eastus"
ACR_NAME="openpolicyacr"
CONTAINER_APP_NAME="openpolicy-api"
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
        error "Azure CLI is not installed. Please install it first: brew install azure-cli"
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

# Function to create a simple Dockerfile for API only
create_simple_dockerfile() {
    log "Creating simple Dockerfile for API deployment..."
    
    cat > Dockerfile.api-simple << 'EOF'
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///./openpolicy.db
ENV REDIS_URL=redis://localhost:6379/0
ENV NODE_ENV=production

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY scrapers/ ./scrapers/
COPY regions_report.json .
COPY policies/ ./policies/

# Create a simple startup script
RUN echo '#!/bin/bash\n\
echo "🚀 Starting OpenPolicy API..."\n\
echo "📅 $(date)"\n\
\n\
# Initialize database schema\n\
echo "📝 Initializing database schema..."\n\
python -c "from src.database.models import Base; from src.database.config import engine; Base.metadata.create_all(bind=engine); print(\"Database schema created\")" || {\n\
    echo "❌ Failed to initialize database schema"\n\
    exit 1\n\
}\n\
\n\
echo "🎯 Starting FastAPI server..."\n\
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload\n\
' > /app/start.sh && chmod +x /app/start.sh

# Create health check script
RUN echo '#!/bin/bash\n\
# Health check for the API\n\
if ! curl -f http://localhost:8000/health >/dev/null 2>&1; then\n\
    echo "API is not responding"\n\
    exit 1\n\
fi\n\
echo "API is healthy"\n\
exit 0\n\
' > /app/healthcheck.sh && chmod +x /app/healthcheck.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /app/healthcheck.sh

# Start the API
CMD ["/app/start.sh"]
EOF

    success "Simple Dockerfile created"
}

# Function to build and push Docker image
build_and_push_image() {
    log "Building Docker image..."
    
    # Check if Dockerfile exists
    if [ ! -f "Dockerfile.api-simple" ]; then
        error "Dockerfile.api-simple not found"
        exit 1
    fi
    
    # Build the image
    docker build -f Dockerfile.api-simple -t "$ACR_NAME.azurecr.io/openpolicy-api:latest" .
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
            --image "$ACR_NAME.azurecr.io/openpolicy-api:latest" \
            --set-env-vars \
                DATABASE_URL="sqlite:///./openpolicy.db" \
                REDIS_URL="redis://localhost:6379/0" \
                CORS_ORIGINS="https://$CONTAINER_APP_NAME.azurecontainerapps.io" \
                NODE_ENV="production"
    else
        # Create new container app
        az containerapp create \
            --name "$CONTAINER_APP_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --environment "$ENVIRONMENT_NAME" \
            --image "$ACR_NAME.azurecr.io/openpolicy-api:latest" \
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
    echo "   API Root: https://$fqdn"
    echo "   Health Check: https://$fqdn/health"
    echo "   API Documentation: https://$fqdn/docs"
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
    if curl -f -s --max-time 30 "https://$fqdn/health" >/dev/null 2>&1; then
        success "Health endpoint is responding"
    else
        warning "Health endpoint is not responding yet (this is normal during startup)"
    fi
    
    # Test root endpoint
    log "Testing root endpoint..."
    if curl -f -s --max-time 30 "https://$fqdn/" >/dev/null 2>&1; then
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
    echo "   # Scale container app"
    echo "   az containerapp revision set-mode --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --mode multiple"
    echo ""
    echo "   # Update container app"
    echo "   az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --image $ACR_NAME.azurecr.io/openpolicy-api:latest"
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
    local summary_file="azure_container_apps_api_summary_${timestamp}.md"
    
    local fqdn=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.configuration.ingress.fqdn" --output tsv)
    local revision=$(az containerapp revision list --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "[0].name" --output tsv)
    
    cat > "$summary_file" << EOF
# Azure Container Apps API Deployment Summary

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

- **API Root:** https://$fqdn
- **Health Check:** https://$fqdn/health
- **API Documentation:** https://$fqdn/docs

## Services Included

1. **FastAPI Backend** - Port 8000
2. **SQLite Database** - Local file
3. **API endpoints**
4. **Health monitoring**

## Management Commands

\`\`\`bash
# View logs
az containerapp logs show --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME

# Check status
az containerapp show --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME

# Scale app
az containerapp revision set-mode --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --mode multiple

# Update app
az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --image $ACR_NAME.azurecr.io/openpolicy-api:latest
\`\`\`

## Next Steps

1. Test the API endpoints
2. Verify the deployment is working
3. Consider adding the dashboard later
4. Set up monitoring and alerts
5. Configure auto-scaling rules

EOF

    success "Deployment summary created: $summary_file"
}

# Main function
main() {
    echo "🚀 Starting Azure Container Apps deployment for OpenPolicy API (Simple)"
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
    
    # Create simple Dockerfile
    create_simple_dockerfile
    
    # Build and push image
    build_and_push_image
    
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
    echo "🎉 Your OpenPolicy API is now running on Azure Container Apps!"
}

# Run main function
main "$@" 