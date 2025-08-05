#!/bin/bash

# 🧪 Comprehensive Deployment Verification Script
# This script tests all components of the OpenPolicy deployment

set -e

# Configuration
RESOURCE_GROUP="openpolicy-rg"
CONTAINER_APP_NAME="openpolicy-api"
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

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local description=$2
    local expected_status=${3:-200}
    
    log "Testing $description..."
    local response=$(curl -s -w "%{http_code}" -o /tmp/response.json "$BASE_URL$endpoint" 2>/dev/null || echo "000")
    local status_code=${response: -3}
    
    if [ "$status_code" = "$expected_status" ]; then
        success "$description is working (Status: $status_code)"
        if [ -s /tmp/response.json ]; then
            echo "   Response: $(cat /tmp/response.json | head -c 200)..."
        fi
    else
        error "$description failed (Status: $status_code)"
        if [ -s /tmp/response.json ]; then
            echo "   Error: $(cat /tmp/response.json | head -c 200)..."
        fi
    fi
    echo ""
}

# Function to check container status
check_container_status() {
    log "Checking container status..."
    
    local status=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.runningStatus" --output tsv 2>/dev/null || echo "Unknown")
    local revision=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.latestReadyRevisionName" --output tsv 2>/dev/null || echo "Unknown")
    local fqdn=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.configuration.ingress.fqdn" --output tsv 2>/dev/null || echo "Unknown")
    
    echo "📊 Container Status:"
    echo "   Status: $status"
    echo "   Revision: $revision"
    echo "   FQDN: $fqdn"
    echo ""
    
    if [ "$status" = "Running" ]; then
        success "Container is running"
    else
        error "Container is not running (Status: $status)"
    fi
}

# Function to check container logs
check_container_logs() {
    log "Checking container logs..."
    
    local log_output=$(az containerapp logs show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --tail 10 2>/dev/null || echo "No logs available")
    
    echo "📋 Recent Logs:"
    echo "$log_output" | head -20
    echo ""
    
    # Check for common error patterns
    if echo "$log_output" | grep -q "ImportError\|ModuleNotFoundError\|TypeError"; then
        error "Found import/module errors in logs"
        return 1
    elif echo "$log_output" | grep -q "Starting FastAPI server"; then
        success "FastAPI server appears to be starting"
    else
        warning "No clear indication of server startup in logs"
    fi
}

# Function to test database connectivity
test_database() {
    log "Testing database connectivity..."
    
    # Test database-related endpoints
    test_endpoint "/stats" "Database statistics endpoint"
    test_endpoint "/jurisdictions" "Jurisdictions endpoint"
    test_endpoint "/representatives" "Representatives endpoint"
    test_endpoint "/bills" "Bills endpoint"
}

# Function to test API endpoints
test_api_endpoints() {
    log "Testing API endpoints..."
    
    # Basic endpoints
    test_endpoint "/health" "Health check endpoint"
    test_endpoint "/docs" "API documentation endpoint"
    test_endpoint "/" "Root endpoint"
    
    # Progress tracking endpoints
    test_endpoint "/api/progress/status" "Progress status endpoint"
    test_endpoint "/api/progress/summary" "Progress summary endpoint"
    test_endpoint "/api/progress/health" "Progress health endpoint"
    
    # Scheduling endpoints
    test_endpoint "/api/scheduling/status" "Scheduling status endpoint"
    
    # Phased loading endpoints
    test_endpoint "/api/phased-loading/status" "Phased loading status endpoint"
}

# Function to test GraphQL
test_graphql() {
    log "Testing GraphQL endpoint..."
    
    local graphql_query='{"query": "{ __schema { types { name } } }"}'
    local response=$(curl -s -X POST -H "Content-Type: application/json" -d "$graphql_query" "$BASE_URL/graphql" 2>/dev/null || echo "{}")
    
    if echo "$response" | grep -q "types"; then
        success "GraphQL endpoint is working"
        echo "   Response: $(echo "$response" | head -c 200)..."
    else
        error "GraphQL endpoint failed"
        echo "   Response: $response"
    fi
    echo ""
}

# Function to test external connectivity
test_external_connectivity() {
    log "Testing external connectivity..."
    
    # Test if the container can reach external services
    local test_urls=(
        "https://httpbin.org/status/200"
        "https://api.github.com"
    )
    
    for url in "${test_urls[@]}"; do
        if curl -s --max-time 10 "$url" >/dev/null 2>&1; then
            success "External connectivity to $url is working"
        else
            warning "External connectivity to $url failed"
        fi
    done
    echo ""
}

# Function to check resource usage
check_resource_usage() {
    log "Checking resource usage..."
    
    local cpu=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.template.containers[0].resources.cpu" --output tsv 2>/dev/null || echo "Unknown")
    local memory=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.template.containers[0].resources.memory" --output tsv 2>/dev/null || echo "Unknown")
    local replicas=$(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.template.scale.minReplicas" --output tsv 2>/dev/null || echo "Unknown")
    
    echo "📊 Resource Configuration:"
    echo "   CPU: $cpu cores"
    echo "   Memory: $memory"
    echo "   Min Replicas: $replicas"
    echo ""
}

# Function to generate verification report
generate_report() {
    local timestamp=$(date +'%Y-%m-%d_%H-%M-%S')
    local report_file="deployment_verification_report_${timestamp}.md"
    
    log "Generating verification report..."
    
    cat > "$report_file" << EOF
# OpenPolicy Deployment Verification Report

**Verification Date:** $(date +'%Y-%m-%d %H:%M:%S')
**Container App:** $CONTAINER_APP_NAME
**Resource Group:** $RESOURCE_GROUP
**Base URL:** $BASE_URL

## Container Status
- **Status:** $(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.runningStatus" --output tsv 2>/dev/null || echo "Unknown")
- **Revision:** $(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.latestReadyRevisionName" --output tsv 2>/dev/null || echo "Unknown")
- **FQDN:** $(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.configuration.ingress.fqdn" --output tsv 2>/dev/null || echo "Unknown")

## Resource Configuration
- **CPU:** $(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.template.containers[0].resources.cpu" --output tsv 2>/dev/null || echo "Unknown") cores
- **Memory:** $(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.template.containers[0].resources.memory" --output tsv 2>/dev/null || echo "Unknown")
- **Min Replicas:** $(az containerapp show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_APP_NAME" --query "properties.template.scale.minReplicas" --output tsv 2>/dev/null || echo "Unknown")

## Test Results
$(cat /tmp/verification_results.txt 2>/dev/null || echo "No test results available")

## Next Steps
1. Review any failed tests
2. Check container logs for errors
3. Verify database connectivity
4. Test all API endpoints
5. Monitor resource usage

EOF

    success "Verification report generated: $report_file"
}

# Main verification function
main() {
    echo "🧪 Starting comprehensive deployment verification..."
    echo "Container App: $CONTAINER_APP_NAME"
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Base URL: $BASE_URL"
    echo ""
    
    # Clear previous results
    > /tmp/verification_results.txt
    
    # Run all verification tests
    check_container_status
    check_container_logs
    check_resource_usage
    test_external_connectivity
    
    # Test endpoints (redirect output to capture results)
    {
        test_api_endpoints
        test_database
        test_graphql
    } | tee -a /tmp/verification_results.txt
    
    # Generate final report
    generate_report
    
    echo ""
    success "Deployment verification completed!"
    echo "📋 Check the verification report for detailed results."
}

# Run main function
main "$@" 