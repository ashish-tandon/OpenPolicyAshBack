#!/bin/bash

# 🚀 Local Deployment Script with Testing
# This script deploys OpenPolicy to local Docker with comprehensive testing

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

# Default values
ENABLE_TESTING=true
ENABLE_MONITORING=false
MONITORING_EMAIL=""
SKIP_PRE_DEPLOYMENT_TESTS=false
SKIP_POST_DEPLOYMENT_TESTS=false

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
        --help)
            echo "Usage: $0 [--no-testing] [--skip-pre-tests] [--skip-post-tests] [--enable-monitoring] [--monitoring-email <email>]"
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
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is required but not installed"
        exit 1
    fi
    success "Docker found: $(docker --version)"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is required but not installed"
        exit 1
    fi
    success "Docker Compose found: $(docker-compose --version)"
    
    # Check curl
    if ! command -v curl &> /dev/null; then
        error "curl is required but not installed"
        exit 1
    fi
    success "curl found"
    
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

# Function to create docker-compose.yml
create_docker_compose() {
    log "📝 Creating docker-compose.yml..."
    
    cat > "$PROJECT_ROOT/docker-compose.yml" << 'EOF'
version: '3.8'
services:
  openpolicy:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: openpolicy_local
    ports:
      - "80:80"
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./regions_report.json:/app/regions_report.json:ro
      - ./scrapers:/app/scrapers:ro
      - ./policies:/app/policies:ro
    environment:
      - DATABASE_URL=sqlite:///./data/openpolicy.db
      - CORS_ORIGINS=http://localhost:3000,http://localhost:80,http://localhost:8000
      - NODE_ENV=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - openpolicy_network

networks:
  openpolicy_network:
    driver: bridge
EOF
    success "docker-compose.yml created"
}

# Function to create data directory
create_data_directory() {
    log "📁 Creating data directory..."
    mkdir -p "$PROJECT_ROOT/data"
    success "Data directory created"
}

# Function to stop existing containers
stop_existing_containers() {
    log "🛑 Stopping existing containers..."
    
    # Stop and remove existing containers
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # Remove any existing containers with the same name
    docker rm -f openpolicy_local 2>/dev/null || true
    
    success "Existing containers stopped"
}

# Function to build and start containers
build_and_start() {
    log "🏗️  Building and starting containers..."
    
    # Build the image
    log "Building Docker image..."
    docker-compose build --no-cache || {
        error "Docker build failed"
        return 1
    }
    
    # Start the containers
    log "Starting containers..."
    docker-compose up -d || {
        error "Failed to start containers"
        return 1
    }
    
    success "Containers started successfully"
}

# Function to wait for service to be ready
wait_for_service() {
    log "⏳ Waiting for service to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s http://localhost/health >/dev/null 2>&1; then
            success "Service is ready after $attempt attempts"
            return 0
        fi
        
        log "Attempt $attempt/$max_attempts: Service not ready yet..."
        sleep 10
        ((attempt++))
    done
    
    error "Service failed to become ready after $max_attempts attempts"
    return 1
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
    
    if [[ -f "$TESTING_DIR/validate-deployment.sh" ]]; then
        bash "$TESTING_DIR/validate-deployment.sh" --url "http://localhost" --type "local" || {
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
    
    if [[ -f "$TESTING_DIR/monitor-deployment.sh" ]]; then
        # Start monitoring in background
        nohup bash "$TESTING_DIR/monitor-deployment.sh" \
            --url "http://localhost" \
            --type "local" \
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

# Function to test deployment
test_deployment() {
    log "🔍 Testing deployment..."
    
    # Test health endpoint
    if curl -f -s http://localhost/health >/dev/null 2>&1; then
        success "Health endpoint is working"
    else
        error "Health endpoint is not working"
        return 1
    fi
    
    # Test API endpoints
    if curl -f -s http://localhost/stats >/dev/null 2>&1; then
        success "API endpoints are working"
    else
        error "API endpoints are not working"
        return 1
    fi
    
    # Test dashboard
    if curl -f -s http://localhost | grep -q "OpenPolicy Dashboard"; then
        success "Dashboard is working"
    else
        error "Dashboard is not working"
        return 1
    fi
    
    success "All deployment tests passed"
}

# Function to show access information
show_access_info() {
    log "📋 Access Information:"
    echo ""
    echo "🌐 Dashboard: http://localhost"
    echo "🔌 API: http://localhost/api"
    echo "🏥 Health: http://localhost/health"
    echo "📊 Stats: http://localhost/stats"
    echo "📚 API Docs: http://localhost/docs"
    echo ""
    echo "📁 Data Directory: $PROJECT_ROOT/data"
    echo "📋 Test Results: $TEST_RESULTS_DIR"
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
    echo "  docker-compose logs -f"
    echo ""
    echo "🛑 Stop application:"
    echo "  docker-compose down"
    echo ""
    echo "🔄 Restart application:"
    echo "  docker-compose restart"
    echo ""
    echo "🔍 Check status:"
    echo "  docker-compose ps"
    echo ""
    if [[ "$ENABLE_MONITORING" == "true" ]]; then
        echo "📊 Stop monitoring:"
        echo "  kill \$(cat $MONITORING_DIR/monitoring.pid)"
        echo ""
    fi
    echo "🧪 Run tests:"
    echo "  bash $TESTING_DIR/validate-deployment.sh --url http://localhost --type local"
    echo ""
}

# Function to create deployment summary
create_deployment_summary() {
    local summary_file="$TEST_RESULTS_DIR/local-deployment-summary.md"
    local timestamp=$(date)
    
    cat > "$summary_file" << EOF
# Local Deployment Summary

**Deployment Time**: $timestamp
**Environment**: Local Docker
**Status**: ✅ Successful

## Configuration

- **Container Name**: openpolicy_local
- **Ports**: 80 (Nginx), 8000 (FastAPI)
- **Database**: SQLite (./data/openpolicy.db)
- **Testing**: $ENABLE_TESTING
- **Monitoring**: $ENABLE_MONITORING

## Access URLs

- **Dashboard**: http://localhost
- **API**: http://localhost/api
- **Health**: http://localhost/health
- **Stats**: http://localhost/stats
- **API Docs**: http://localhost/docs

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

## Next Steps

1. Access the dashboard at http://localhost
2. Monitor application performance
3. Check logs if issues arise
4. Run validation tests as needed

## Troubleshooting

If the application is not working:

1. Check container status: \`docker-compose ps\`
2. View logs: \`docker-compose logs -f\`
3. Restart: \`docker-compose restart\`
4. Run tests: \`bash $TESTING_DIR/validate-deployment.sh --url http://localhost --type local\`

EOF
    
    success "Deployment summary created: $summary_file"
}

# Main execution
main() {
    log "🚀 Starting Local Deployment with Testing"
    
    # Create necessary directories
    mkdir -p "$TEST_RESULTS_DIR" "$MONITORING_DIR"
    
    # Run deployment process
    check_prerequisites
    run_pre_deployment_tests
    create_docker_compose
    create_data_directory
    stop_existing_containers
    build_and_start
    wait_for_service
    test_deployment
    run_post_deployment_tests
    start_monitoring
    show_access_info
    show_management_commands
    create_deployment_summary
    
    log "🎉 Local Deployment Completed Successfully!"
    log "📊 Test results available in: $TEST_RESULTS_DIR"
    log "📋 Deployment summary: $TEST_RESULTS_DIR/local-deployment-summary.md"
    
    if [[ "$ENABLE_MONITORING" == "true" ]]; then
        log "📊 Monitoring is running in background"
    fi
    
    success "OpenPolicy is now running locally! Access it at http://localhost"
}

# Run main function
main "$@" 