#!/bin/bash

# Verify and Deploy to QNAP Container Station
# First verifies Container Station is working, then deploys OpenPolicy

set -e

# Configuration
QNAP_HOST="192.168.2.152"
QNAP_PORT="22"
QNAP_USER="ashish101"
QNAP_PASS="Pergola@41"
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

# Function to verify Container Station
verify_container_station() {
    log "Verifying Container Station installation..."
    
    # Test SSH connection and check for Docker
    if sshpass -p "${QNAP_PASS}" ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "which docker"; then
        success "Docker is available on QNAP"
        
        # Check Docker version
        log "Checking Docker version..."
        sshpass -p "${QNAP_PASS}" ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "docker --version"
        
        # Check if Docker daemon is running
        log "Checking Docker daemon status..."
        if sshpass -p "${QNAP_PASS}" ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "docker info >/dev/null 2>&1"; then
            success "Docker daemon is running"
        else
            error "Docker daemon is not running"
            return 1
        fi
        
        # Check for docker-compose
        log "Checking docker-compose..."
        if sshpass -p "${QNAP_PASS}" ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "which docker-compose"; then
            success "Docker Compose is available"
            sshpass -p "${QNAP_PASS}" ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "docker-compose --version"
        else
            warning "Docker Compose not found, will install it"
            install_docker_compose
        fi
        
        return 0
    else
        error "Docker is not available on QNAP"
        return 1
    fi
}

# Function to install docker-compose
install_docker_compose() {
    log "Installing Docker Compose on QNAP..."
    
    sshpass -p "${QNAP_PASS}" ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "
        if ! command -v docker-compose &> /dev/null; then
            echo 'Installing Docker Compose...'
            curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose
            chmod +x /usr/local/bin/docker-compose
            
            if [ ! -f /usr/bin/docker-compose ]; then
                ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
            fi
            
            echo 'Docker Compose installed successfully'
            docker-compose --version
        fi
    "
}

# Function to create deployment script
create_deployment_script() {
    log "Creating deployment script..."
    
    cat > qnap-deploy-verified.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting verified QNAP deployment..."

# Verify Docker is working
echo "🔍 Verifying Docker..."
docker --version
docker info >/dev/null 2>&1 || { echo "❌ Docker daemon not running"; exit 1; }

# Stop and remove existing container
echo "📦 Stopping existing container..."
docker stop openpolicy_single 2>/dev/null || true
docker rm openpolicy_single 2>/dev/null || true

# Remove old image
echo "🗑️ Removing old image..."
docker rmi ashishtandon/openpolicy-single:latest 2>/dev/null || true

# Pull latest image
echo "⬇️ Pulling latest image from Docker Hub..."
if docker pull ashishtandon/openpolicy-single:latest; then
    echo "✅ Image pulled successfully"
else
    echo "❌ Failed to pull image from Docker Hub"
    echo "This might be because the image doesn't exist yet or network issues"
    echo "You may need to build and push the image to Docker Hub first"
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
      - CORS_ORIGINS=http://localhost:3000,http://localhost:80,http://192.168.2.152,http://ashishsnas.myqnapcloud.com
      - NODE_ENV=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  postgres_data:
    driver: local
COMPOSE_EOF

# Start the container using docker-compose
echo "🚀 Starting the container..."
if docker-compose up -d; then
    echo "✅ Container started successfully with docker-compose"
else
    echo "❌ Failed to start container with docker-compose"
    echo "Trying direct docker run..."
    
    # Fallback to direct docker run
    docker run -d \
        --name openpolicy_single \
        --restart unless-stopped \
        -p 80:80 \
        -p 8000:8000 \
        -p 3000:3000 \
        -p 5555:5555 \
        -p 6379:6379 \
        -p 5432:5432 \
        -e DATABASE_URL=postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata \
        -e REDIS_URL=redis://localhost:6379/0 \
        -e CORS_ORIGINS=http://localhost:3000,http://localhost:80,http://192.168.2.152,http://ashishsnas.myqnapcloud.com \
        -e NODE_ENV=production \
        -v postgres_data:/var/lib/postgresql/data \
        ashishtandon/openpolicy-single:latest
    
    if [ $? -eq 0 ]; then
        echo "✅ Container started successfully with docker run"
    else
        echo "❌ Failed to start container"
        exit 1
    fi
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
            echo "Container logs:"
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
            echo "Container logs:"
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

    chmod +x qnap-deploy-verified.sh
    success "Deployment script created"
}

# Function to deploy to QNAP
deploy_to_qnap() {
    log "Deploying to QNAP..."
    
    # Create deployment script
    create_deployment_script
    
    # Copy script to QNAP
    log "Copying deployment script to QNAP..."
    if sshpass -p "${QNAP_PASS}" scp -o ConnectTimeout=10 -P ${QNAP_PORT} qnap-deploy-verified.sh ${QNAP_USER}@${QNAP_HOST}:/tmp/; then
        success "Deployment script copied to QNAP"
    else
        error "Failed to copy deployment script to QNAP"
        exit 1
    fi
    
    # Execute deployment on QNAP
    log "Executing deployment on QNAP..."
    if sshpass -p "${QNAP_PASS}" ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "bash /tmp/qnap-deploy-verified.sh"; then
        success "Successfully deployed to QNAP"
    else
        error "Failed to deploy to QNAP"
        exit 1
    fi
    
    # Clean up local script
    rm qnap-deploy-verified.sh
}

# Function to monitor deployment
monitor_deployment() {
    log "Monitoring deployment..."
    
    # Wait a bit for services to stabilize
    sleep 10
    
    # Test API using IP
    log "Testing QNAP API (IP: ${QNAP_HOST})..."
    if curl -f -s --max-time 10 http://${QNAP_HOST}:8000/health >/dev/null 2>&1; then
        success "QNAP API is responding"
    else
        warning "QNAP API health check failed"
    fi
    
    # Test dashboard using IP
    log "Testing QNAP Dashboard (IP: ${QNAP_HOST})..."
    if curl -f -s --max-time 10 http://${QNAP_HOST}:3000 >/dev/null 2>&1; then
        success "QNAP Dashboard is responding"
    else
        warning "QNAP Dashboard health check failed"
    fi
    
    # Test main entry point
    log "Testing main entry point (IP: ${QNAP_HOST})..."
    if curl -f -s --max-time 10 http://${QNAP_HOST} >/dev/null 2>&1; then
        success "Main entry point is responding"
    else
        warning "Main entry point health check failed"
    fi
    
    success "Deployment monitoring completed"
}

# Function to show container status
show_container_status() {
    log "Checking container status on QNAP..."
    
    if sshpass -p "${QNAP_PASS}" ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "docker ps | grep ${CONTAINER_NAME}"; then
        success "Container is running on QNAP"
    else
        error "Container is not running on QNAP"
    fi
}

# Function to show logs
show_logs() {
    log "Showing recent container logs..."
    
    sshpass -p "${QNAP_PASS}" ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "docker logs --tail 20 ${CONTAINER_NAME}" || {
        warning "Could not retrieve container logs"
    }
}

# Function to show access URLs
show_access_urls() {
    log "Access URLs:"
    echo "🌐 Main Dashboard: http://${QNAP_HOST}"
    echo "📊 API Documentation: http://${QNAP_HOST}:8000/docs"
    echo "🏥 Health Check: http://${QNAP_HOST}:8000/health"
    echo "🌺 Flower Monitor: http://${QNAP_HOST}:5555"
    echo "🗄️ Direct API: http://${QNAP_HOST}:8000"
    echo "🖥️ Direct Dashboard: http://${QNAP_HOST}:3000"
    echo ""
    echo "🌐 Domain Access (if available):"
    echo "🌐 Main Dashboard: https://ashishsnas.myqnapcloud.com"
    echo "📊 API Documentation: https://ashishsnas.myqnapcloud.com/api/docs"
    echo "🏥 Health Check: https://ashishsnas.myqnapcloud.com/health"
    echo ""
    echo "📱 Container Station Access:"
    echo "🔧 Container Station UI: http://${QNAP_HOST}:8080"
    echo "📊 Container Management: http://${QNAP_HOST}:8080/container-station/"
}

# Main function
main() {
    log "🔍 Starting QNAP Container Station Verification and Deployment"
    log "Host: ${QNAP_HOST}"
    log "Username: ${QNAP_USER}"
    
    # First verify Container Station
    if verify_container_station; then
        success "Container Station verification passed"
        
        # Deploy to QNAP
        deploy_to_qnap
        
        # Monitor deployment
        monitor_deployment
        
        # Show container status
        show_container_status
        
        # Show logs
        show_logs
        
        # Show access URLs
        show_access_urls
        
        log "🎉 QNAP deployment completed successfully!"
        log "Access your application at: http://${QNAP_HOST}/"
        log "Manage containers at: http://${QNAP_HOST}:8080/container-station/"
    else
        error "Container Station verification failed"
        log "Please ensure Container Station is properly installed and running"
        log "You can access Container Station at: http://${QNAP_HOST}:8080/container-station/"
    fi
}

# Run main function
main "$@" 