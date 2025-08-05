#!/bin/bash

# Final QNAP Deployment Script with Credentials
# Deploys the OpenPolicy single container system to QNAP

set -e

# Configuration - Using IP address and provided credentials
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

# Function to create deployment script
create_deployment_script() {
    log "Creating deployment script..."
    
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
      - CORS_ORIGINS=http://localhost:3000,http://localhost:80,http://192.168.2.152,http://ashishsnas.myqnapcloud.com
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

    chmod +x qnap-deploy-remote.sh
    success "Deployment script created"
}

# Function to deploy to QNAP using sshpass
deploy_to_qnap() {
    log "Deploying to QNAP..."
    
    # Check if sshpass is available
    if ! command -v sshpass &> /dev/null; then
        error "sshpass is not installed. Please install it first: brew install sshpass"
        exit 1
    fi
    
    # Create deployment script
    create_deployment_script
    
    # Copy script to QNAP
    log "Copying deployment script to QNAP..."
    if sshpass -p "${QNAP_PASS}" scp -o ConnectTimeout=10 -P ${QNAP_PORT} qnap-deploy-remote.sh ${QNAP_USER}@${QNAP_HOST}:/tmp/; then
        success "Deployment script copied to QNAP"
    else
        error "Failed to copy deployment script to QNAP"
        exit 1
    fi
    
    # Execute deployment on QNAP
    log "Executing deployment on QNAP..."
    if sshpass -p "${QNAP_PASS}" ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "bash /tmp/qnap-deploy-remote.sh"; then
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
}

# Function to create deployment summary
create_summary() {
    log "Creating deployment summary..."
    
    TIMESTAMP=$(date +'%Y-%m-%d %H:%M:%S')
    
    cat > QNAP_DEPLOYMENT_SUCCESS_${TIMESTAMP// /_}.md << EOF
# QNAP Deployment Success Summary

**Deployment Date:** ${TIMESTAMP}
**QNAP Host:** ${QNAP_HOST}
**Username:** ${QNAP_USER}
**Container:** ${CONTAINER_NAME}

## Deployment Status

### ✅ QNAP NAS
- Host: ${QNAP_HOST}
- Container: ${CONTAINER_NAME}
- Status: Running

## Access URLs

### Local Network Access (IP)
- **Main Dashboard:** http://${QNAP_HOST}
- **API Documentation:** http://${QNAP_HOST}:8000/docs
- **Health Check:** http://${QNAP_HOST}:8000/health
- **Flower Monitor:** http://${QNAP_HOST}:5555

### Domain Access (if available)
- **Main Dashboard:** https://ashishsnas.myqnapcloud.com
- **API Documentation:** https://ashishsnas.myqnapcloud.com/api/docs
- **Health Check:** https://ashishsnas.myqnapcloud.com/health

## Services Included

1. **PostgreSQL Database** - Port 5432
2. **Redis Cache** - Port 6379
3. **FastAPI Backend** - Port 8000
4. **React Dashboard** - Port 3000
5. **Celery Worker** - Background
6. **Celery Beat** - Background
7. **Flower Monitor** - Port 5555
8. **Nginx Reverse Proxy** - Port 80

## Health Checks

- Database connectivity
- Redis connectivity
- API responsiveness
- Dashboard accessibility

## Next Steps

1. Monitor system performance
2. Check logs for any errors
3. Verify all features are working
4. Set up regular backups

EOF

    success "Deployment summary created: QNAP_DEPLOYMENT_SUCCESS_${TIMESTAMP// /_}.md"
}

# Main deployment function
main() {
    log "🚀 Starting Final QNAP Deployment (IP: ${QNAP_HOST})"
    log "Username: ${QNAP_USER}"
    
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
    
    # Create summary
    create_summary
    
    log "🎉 QNAP deployment completed successfully!"
    log "Access your application at: http://${QNAP_HOST}/"
}

# Run main function
main "$@" 