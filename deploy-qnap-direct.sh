#!/bin/bash

# Direct QNAP Deployment Script
# Deploys the OpenPolicy single container system to QNAP

set -e

# Configuration
QNAP_HOST="ashishsnas.myqnapcloud.com"
QNAP_PORT="22"
QNAP_USER="admin"
CONTAINER_NAME="openpolicy_single"

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

# Function to test SSH connection
test_ssh_connection() {
    log "Testing SSH connection to QNAP..."
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "echo 'SSH connection successful'"; then
        success "SSH connection to QNAP established"
        return 0
    else
        error "Failed to establish SSH connection to QNAP"
        return 1
    fi
}

# Function to deploy to QNAP
deploy_to_qnap() {
    log "Deploying to QNAP..."
    
    # Create deployment script for QNAP
    cat > qnap-deploy-remote.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting QNAP deployment..."

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed on QNAP"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed on QNAP"
    exit 1
fi

# Stop and remove existing container
echo "📦 Stopping existing container..."
docker stop openpolicy_single 2>/dev/null || true
docker rm openpolicy_single 2>/dev/null || true

# Remove old image
echo "🗑️ Removing old image..."
docker rmi ashishtandon/openpolicy-single:latest 2>/dev/null || true

# Pull latest image
echo "⬇️ Pulling latest image..."
if docker pull ashishtandon/openpolicy-single:latest; then
    echo "✅ Image pulled successfully"
else
    echo "❌ Failed to pull image"
    exit 1
fi

# Create docker-compose file
echo "📝 Creating docker-compose configuration..."
cat > docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  openpolicy:
    image: ashishtandon/openpolicy-single:latest
    container_name: openpolicy_single
    ports:
      - "80:80"
      - "8000:8000"
      - "3000:3000"
      - "5555:5555"
      - "6379:6379"
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - DATABASE_URL=postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata
      - REDIS_URL=redis://localhost:6379/0
      - CORS_ORIGINS=http://localhost:3000,http://localhost:80,http://ashishsnas.myqnapcloud.com
      - NODE_ENV=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "/app/healthcheck.sh"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  postgres_data:
    driver: local
COMPOSE_EOF

# Start the container
echo "🚀 Starting the container..."
if docker-compose up -d; then
    echo "✅ Container started successfully"
else
    echo "❌ Failed to start container"
    exit 1
fi

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Test health endpoint
echo "🏥 Testing health endpoint..."
for i in {1..10}; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ API health check passed"
        break
    else
        echo "   Attempt $i/10 - API not ready yet..."
        if [ $i -eq 10 ]; then
            echo "❌ API health check failed after 10 attempts"
            docker logs openpolicy_single
            exit 1
        fi
        sleep 10
    fi
done

# Test dashboard
echo "🖥️ Testing dashboard..."
for i in {1..5}; do
    if curl -f http://localhost:3000 >/dev/null 2>&1; then
        echo "✅ Dashboard health check passed"
        break
    else
        echo "   Attempt $i/5 - Dashboard not ready yet..."
        if [ $i -eq 5 ]; then
            echo "❌ Dashboard health check failed after 5 attempts"
            docker logs openpolicy_single
            exit 1
        fi
        sleep 10
    fi
done

# Show container status
echo "📊 Container status:"
docker ps | grep openpolicy_single

echo "✅ QNAP deployment completed successfully"
EOF

    # Make script executable
    chmod +x qnap-deploy-remote.sh
    
    # Copy script to QNAP
    log "Copying deployment script to QNAP..."
    if scp -o ConnectTimeout=10 -P ${QNAP_PORT} qnap-deploy-remote.sh ${QNAP_USER}@${QNAP_HOST}:/tmp/; then
        success "Deployment script copied to QNAP"
    else
        error "Failed to copy deployment script to QNAP"
        exit 1
    fi
    
    # Execute deployment on QNAP
    log "Executing deployment on QNAP..."
    if ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "bash /tmp/qnap-deploy-remote.sh"; then
        success "Successfully deployed to QNAP"
    else
        error "Failed to deploy to QNAP"
        exit 1
    fi
    
    # Clean up local script
    rm qnap-deploy-remote.sh
}

# Function to monitor deployment
monitor_deployment() {
    log "Monitoring deployment..."
    
    # Wait a bit for services to stabilize
    sleep 10
    
    # Test API
    log "Testing QNAP API..."
    if curl -f -s --max-time 10 https://${QNAP_HOST}/health >/dev/null 2>&1; then
        success "QNAP API is responding"
    else
        warning "QNAP API health check failed"
    fi
    
    # Test dashboard
    log "Testing QNAP Dashboard..."
    if curl -f -s --max-time 10 https://${QNAP_HOST}/ >/dev/null 2>&1; then
        success "QNAP Dashboard is responding"
    else
        warning "QNAP Dashboard health check failed"
    fi
    
    success "Deployment monitoring completed"
}

# Function to show container status
show_container_status() {
    log "Checking container status on QNAP..."
    
    if ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "docker ps | grep ${CONTAINER_NAME}"; then
        success "Container is running on QNAP"
    else
        error "Container is not running on QNAP"
    fi
}

# Function to show logs
show_logs() {
    log "Showing recent container logs..."
    
    ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "docker logs --tail 20 ${CONTAINER_NAME}" || {
        warning "Could not retrieve container logs"
    }
}

# Main deployment function
main() {
    log "🚀 Starting Direct QNAP Deployment"
    
    # Test SSH connection
    if ! test_ssh_connection; then
        error "Cannot proceed without SSH connection to QNAP"
        exit 1
    fi
    
    # Deploy to QNAP
    deploy_to_qnap
    
    # Monitor deployment
    monitor_deployment
    
    # Show container status
    show_container_status
    
    # Show logs
    show_logs
    
    log "🎉 QNAP deployment completed!"
    log "Access your application at: https://${QNAP_HOST}/"
}

# Run main function
main "$@" 