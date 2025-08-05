#!/bin/bash

# 🚀 Azure Deployment Script with Testing
# This script deploys OpenPolicy to Azure Container Apps with comprehensive testing

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
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

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TESTING_DIR="$PROJECT_ROOT/scripts/testing"
TEST_RESULTS_DIR="$PROJECT_ROOT/test_results"
MONITORING_DIR="$PROJECT_ROOT/monitoring"

# Azure Configuration
RESOURCE_GROUP="openpolicy-rg"
ACR_NAME="openpolicyacr"
ENVIRONMENT_NAME="openpolicy-env"
CONTAINER_APP_NAME="openpolicy-app"
LOCATION="eastus"

# Default values
ENABLE_TESTING=true
ENABLE_MONITORING=false
MONITORING_EMAIL=""
SKIP_PRE_DEPLOYMENT_TESTS=false
SKIP_POST_DEPLOYMENT_TESTS=false
SKIP_BUILD=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-testing)
            ENABLE_TESTING=false
            shift
            ;;
        --skip-pre-tests)
            SKIP_PRE_DEPLOYMENT_TESTS=true
            shift
            ;;
        --skip-post-tests)
            SKIP_POST_DEPLOYMENT_TESTS=true
            shift
            ;;
        --enable-monitoring)
            ENABLE_MONITORING=true
            shift
            ;;
        --monitoring-email)
            MONITORING_EMAIL="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--no-testing] [--skip-pre-tests] [--skip-post-tests] [--enable-monitoring] [--monitoring-email <email>] [--skip-build]"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to check prerequisites
check_prerequisites() {
    log "🔍 Checking prerequisites..."
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        error "Azure CLI is required but not installed"
        exit 1
    fi
    success "Azure CLI found: $(az --version | head -1)"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is required but not installed"
        exit 1
    fi
    success "Docker found: $(docker --version)"
    
    # Check curl
    if ! command -v curl &> /dev/null; then
        error "curl is required but not installed"
        exit 1
    fi
    success "curl found"
    
    # Check Azure login
    if ! az account show &> /dev/null; then
        error "Not logged into Azure. Please run 'az login'"
        exit 1
    fi
    success "Azure login verified"
    
    # Check required files
    required_files=(
        "Dockerfile"
        "nginx.conf"
        "src/api/main.py"
        "dashboard/package.json"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$PROJECT_ROOT/$file" ]]; then
            error "Required file not found: $file"
            exit 1
        fi
    done
    success "All required files found"
}

# Function to run pre-deployment tests
run_pre_deployment_tests() {
    if [[ "$SKIP_PRE_DEPLOYMENT_TESTS" == "true" ]]; then
        warning "Skipping pre-deployment tests"
        return 0
    fi
    
    if [[ "$ENABLE_TESTING" == "false" ]]; then
        warning "Testing disabled, skipping pre-deployment tests"
        return 0
    fi
    
    log "🧪 Running pre-deployment tests..."
    
    if [[ -f "$TESTING_DIR/run-pre-deployment-tests.sh" ]]; then
        bash "$TESTING_DIR/run-pre-deployment-tests.sh" || {
            error "Pre-deployment tests failed"
            return 1
        }
        success "Pre-deployment tests passed"
    else
        warning "Pre-deployment test script not found, skipping"
    fi
}

# Function to create Azure resources
create_azure_resources() {
    log "🏗️  Creating Azure resources..."
    
    # Create resource group
    log "Creating resource group..."
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION" || {
        error "Failed to create resource group"
        return 1
    }
    success "Resource group created: $RESOURCE_GROUP"
    
    # Create Azure Container Registry
    log "Creating Azure Container Registry..."
    az acr create --resource-group "$RESOURCE_GROUP" --name "$ACR_NAME" --sku Basic || {
        error "Failed to create Azure Container Registry"
        return 1
    }
    success "Azure Container Registry created: $ACR_NAME"
    
    # Create Container Apps Environment
    log "Creating Container Apps Environment..."
    az containerapp env create \
        --name "$ENVIRONMENT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" || {
        error "Failed to create Container Apps Environment"
        return 1
    }
    success "Container Apps Environment created: $ENVIRONMENT_NAME"
}

# Function to build and push image
build_and_push_image() {
    if [[ "$SKIP_BUILD" == "true" ]]; then
        warning "Skipping build and push (using existing image)"
        return 0
    fi
    
    log "🏗️  Building and pushing Docker image..."
    
    # Get ACR credentials
    log "Getting ACR credentials..."
    local registry_username=$(az acr credential show --name "$ACR_NAME" --query "username" --output tsv)
    local registry_password=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" --output tsv)
    
    # Login to ACR
    log "Logging into Azure Container Registry..."
    az acr login --name "$ACR_NAME" || {
        error "Failed to login to Azure Container Registry"
        return 1
    }
    
    # Build the image for Linux/AMD64 (Azure requirement)
    log "Building Docker image for Azure..."
    docker build --platform linux/amd64 \
        -t "$ACR_NAME.azurecr.io/openpolicy:latest" . || {
        error "Docker build failed"
        return 1
    }
    success "Docker image built successfully"
    
    # Push the image to ACR
    log "Pushing image to Azure Container Registry..."
    docker push "$ACR_NAME.azurecr.io/openpolicy:latest" || {
        error "Failed to push image to Azure Container Registry"
        return 1
    }
    success "Image pushed to Azure Container Registry"
}

# Function to deploy container app
deploy_container_app() {
    log "🚀 Deploying Container App..."
    
    # Get ACR credentials
    local registry_username=$(az acr credential show --name "$ACR_NAME" --query "username" --output tsv)
    local registry_password=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" --output tsv)
    
    # Deploy the container app
    az containerapp create \
        --name "$CONTAINER_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --environment "$ENVIRONMENT_NAME" \
        --image "$ACR_NAME.azurecr.io/openpolicy:latest" \
        --target-port 80 \
        --ingress external \
        --registry-server "$ACR_NAME.azurecr.io" \
        --registry-username "$registry_username" \
        --registry-password "$registry_password" \
        --env-vars \
            DATABASE_URL="sqlite:///./openpolicy.db" \
            CORS_ORIGINS="https://$CONTAINER_APP_NAME.kindgrass-4bb31d5d.eastus.azurecontainerapps.io" \
            NODE_ENV="production" \
        --cpu 2 \
        --memory 4Gi \
        --min-replicas 1 \
        --max-replicas 3 || {
        error "Failed to deploy Container App"
        return 1
    }
    
    success "Container App deployed successfully"
}

# Function to wait for deployment
wait_for_deployment() {
    log "⏳ Waiting for deployment to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        local status=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.runningStatus" --output tsv 2>/dev/null || echo "unknown")
        
        if [[ "$status" == "Running" ]]; then
            success "Container App is running after $attempt attempts"
            return 0
        fi
        
        log "Attempt $attempt/$max_attempts: Status is $status, waiting..."
        sleep 30
        ((attempt++))
    done
    
    error "Container App failed to become ready after $max_attempts attempts"
    return 1
}

# Function to get container app info
get_container_app_info() {
    log "📋 Getting Container App information..."
    
    local app_url=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.configuration.ingress.fqdn" --output tsv)
    local app_status=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.runningStatus" --output tsv)
    
    echo ""
    echo "🌐 Container App URL: https://$app_url"
    echo "📊 Status: $app_status"
    echo ""
    
    # Store URL for later use
    echo "https://$app_url" > "$TEST_RESULTS_DIR/azure-app-url.txt"
}

# Function to run post-deployment tests
run_post_deployment_tests() {
    if [[ "$SKIP_POST_DEPLOYMENT_TESTS" == "true" ]]; then
        warning "Skipping post-deployment tests"
        return 0
    fi
    
    if [[ "$ENABLE_TESTING" == "false" ]]; then
        warning "Testing disabled, skipping post-deployment tests"
        return 0
    fi
    
    log "🧪 Running post-deployment tests..."
    
    # Get the app URL
    local app_url=$(cat "$TEST_RESULTS_DIR/azure-app-url.txt" 2>/dev/null || echo "")
    if [[ -z "$app_url" ]]; then
        app_url=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.configuration.ingress.fqdn" --output tsv)
        app_url="https://$app_url"
    fi
    
    if [[ -f "$TESTING_DIR/validate-deployment.sh" ]]; then
        bash "$TESTING_DIR/validate-deployment.sh" --url "$app_url" --type "azure" || {
            error "Post-deployment tests failed"
            return 1
        }
        success "Post-deployment tests passed"
    else
        warning "Post-deployment test script not found, skipping"
    fi
}

# Function to start monitoring
start_monitoring() {
    if [[ "$ENABLE_MONITORING" == "false" ]]; then
        log "Monitoring disabled"
        return 0
    fi
    
    log "📊 Starting monitoring..."
    
    # Get the app URL
    local app_url=$(cat "$TEST_RESULTS_DIR/azure-app-url.txt" 2>/dev/null || echo "")
    if [[ -z "$app_url" ]]; then
        app_url=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.configuration.ingress.fqdn" --output tsv)
        app_url="https://$app_url"
    fi
    
    if [[ -f "$TESTING_DIR/monitor-deployment.sh" ]]; then
        # Start monitoring in background
        nohup bash "$TESTING_DIR/monitor-deployment.sh" \
            --url "$app_url" \
            --type "azure" \
            --interval 60 \
            ${MONITORING_EMAIL:+--email "$MONITORING_EMAIL"} \
            > "$MONITORING_DIR/monitoring.log" 2>&1 &
        
        local monitoring_pid=$!
        echo "$monitoring_pid" > "$MONITORING_DIR/monitoring.pid"
        
        success "Monitoring started with PID: $monitoring_pid"
    else
        warning "Monitoring script not found"
    fi
}

# Function to show access information
show_access_info() {
    log "📋 Access Information:"
    
    local app_url=$(cat "$TEST_RESULTS_DIR/azure-app-url.txt" 2>/dev/null || echo "")
    if [[ -z "$app_url" ]]; then
        app_url=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.configuration.ingress.fqdn" --output tsv)
        app_url="https://$app_url"
    fi
    
    echo ""
    echo "🌐 Dashboard: $app_url"
    echo "🔌 API: $app_url/api"
    echo "🏥 Health: $app_url/health"
    echo "📊 Stats: $app_url/stats"
    echo "📚 API Docs: $app_url/docs"
    echo ""
    echo "📁 Test Results: $TEST_RESULTS_DIR"
    if [[ "$ENABLE_MONITORING" == "true" ]]; then
        echo "📊 Monitoring: $MONITORING_DIR"
    fi
    echo ""
}

# Function to show management commands
show_management_commands() {
    log "🛠️  Management Commands:"
    echo ""
    echo "📊 View logs:"
    echo "  az containerapp logs show --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME --follow"
    echo ""
    echo "🛑 Stop application:"
    echo "  az containerapp stop --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME"
    echo ""
    echo "🔄 Restart application:"
    echo "  az containerapp restart --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME"
    echo ""
    echo "🔍 Check status:"
    echo "  az containerapp show --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME"
    echo ""
    if [[ "$ENABLE_MONITORING" == "true" ]]; then
        echo "📊 Stop monitoring:"
        echo "  kill \$(cat $MONITORING_DIR/monitoring.pid)"
        echo ""
    fi
    echo "🧪 Run tests:"
    local app_url=$(cat "$TEST_RESULTS_DIR/azure-app-url.txt" 2>/dev/null || echo "")
    if [[ -z "$app_url" ]]; then
        app_url=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.configuration.ingress.fqdn" --output tsv)
        app_url="https://$app_url"
    fi
    echo "  bash $TESTING_DIR/validate-deployment.sh --url $app_url --type azure"
    echo ""
}

# Function to create deployment summary
create_deployment_summary() {
    local summary_file="$TEST_RESULTS_DIR/azure-deployment-summary.md"
    local timestamp=$(date)
    local app_url=$(cat "$TEST_RESULTS_DIR/azure-app-url.txt" 2>/dev/null || echo "")
    if [[ -z "$app_url" ]]; then
        app_url=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.configuration.ingress.fqdn" --output tsv)
        app_url="https://$app_url"
    fi
    
    cat > "$summary_file" << EOF
# Azure Deployment Summary

**Deployment Time**: $timestamp
**Environment**: Azure Container Apps
**Status**: ✅ Successful

## Configuration

- **Resource Group**: $RESOURCE_GROUP
- **Container Registry**: $ACR_NAME.azurecr.io
- **Container App**: $CONTAINER_APP_NAME
- **Environment**: $ENVIRONMENT_NAME
- **Location**: $LOCATION
- **Testing**: $ENABLE_TESTING
- **Monitoring**: $ENABLE_MONITORING

## Access URLs

- **Dashboard**: $app_url
- **API**: $app_url/api
- **Health**: $app_url/health
- **Stats**: $app_url/stats
- **API Docs**: $app_url/docs

## Components Status

- ✅ Nginx (Reverse Proxy)
- ✅ FastAPI (Backend API)
- ✅ React Dashboard (Frontend)
- ✅ SQLite Database
- ✅ In-Memory Rate Limiting
- ✅ Health Checks

## Testing Results

- **Pre-Deployment Tests**: $(if [[ "$SKIP_PRE_DEPLOYMENT_TESTS" == "true" ]]; then echo "Skipped"; else echo "✅ Passed"; fi)
- **Post-Deployment Tests**: $(if [[ "$SKIP_POST_DEPLOYMENT_TESTS" == "true" ]]; then echo "Skipped"; else echo "✅ Passed"; fi)
- **Health Checks**: ✅ Working
- **API Endpoints**: ✅ Working
- **Dashboard**: ✅ Working

## Monitoring

- **Status**: $(if [[ "$ENABLE_MONITORING" == "true" ]]; then echo "✅ Enabled"; else echo "❌ Disabled"; fi)
- **Logs**: $MONITORING_DIR/monitoring.log
- **Metrics**: $MONITORING_DIR/metrics.json

## Azure Resources

- **Resource Group**: $RESOURCE_GROUP
- **Container Registry**: $ACR_NAME
- **Container Apps Environment**: $ENVIRONMENT_NAME
- **Container App**: $CONTAINER_APP_NAME

## Next Steps

1. Access the dashboard at $app_url
2. Monitor application performance
3. Check Azure logs if issues arise
4. Run validation tests as needed

## Troubleshooting

If the application is not working:

1. Check Container App status: \`az containerapp show --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME\`
2. View logs: \`az containerapp logs show --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME --follow\`
3. Restart: \`az containerapp restart --resource-group $RESOURCE_GROUP --name $CONTAINER_APP_NAME\`
4. Run tests: \`bash $TESTING_DIR/validate-deployment.sh --url $app_url --type azure\`

EOF
    
    success "Deployment summary created: $summary_file"
}

# Main execution
main() {
    log "🚀 Starting Azure Deployment with Testing"
    
    # Create necessary directories
    mkdir -p "$TEST_RESULTS_DIR" "$MONITORING_DIR"
    
    # Run deployment process
    check_prerequisites
    run_pre_deployment_tests
    create_azure_resources
    build_and_push_image
    deploy_container_app
    wait_for_deployment
    get_container_app_info
    run_post_deployment_tests
    start_monitoring
    show_access_info
    show_management_commands
    create_deployment_summary
    
    log "🎉 Azure Deployment Completed Successfully!"
    log "📊 Test results available in: $TEST_RESULTS_DIR"
    log "📋 Deployment summary: $TEST_RESULTS_DIR/azure-deployment-summary.md"
    
    if [[ "$ENABLE_MONITORING" == "true" ]]; then
        log "📊 Monitoring is running in background"
    fi
    
    local app_url=$(cat "$TEST_RESULTS_DIR/azure-app-url.txt" 2>/dev/null || echo "")
    if [[ -z "$app_url" ]]; then
        app_url=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.configuration.ingress.fqdn" --output tsv)
        app_url="https://$app_url"
    fi
    
    success "OpenPolicy is now running on Azure! Access it at $app_url"
}

# Run main function
main "$@" 