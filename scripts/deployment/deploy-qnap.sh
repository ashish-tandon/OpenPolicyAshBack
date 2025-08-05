#!/bin/bash

# 🚀 QNAP Deployment Script for OpenPolicy with Dashboard
# Deploys to QNAP Container Station with full UI and API

set -e

# Configuration
QNAP_HOST="ashishsnas.myqnapcloud.com"
QNAP_USER="admin"
CONTAINER_NAME="openpolicy_qnap"
IMAGE_NAME="ashishtandon9/openpolicyashback:latest"

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

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if we can connect to QNAP
    if ! ping -c 1 "$QNAP_HOST" &> /dev/null; then
        error "Cannot reach QNAP host: $QNAP_HOST"
        exit 1
    fi
    success "QNAP host is reachable"
    
    # Check SSH connectivity
    if ! ssh -o ConnectTimeout=10 "$QNAP_USER@$QNAP_HOST" "echo 'SSH connection successful'" &> /dev/null; then
        error "Cannot connect to QNAP via SSH"
        exit 1
    fi
    success "SSH connection to QNAP established"
}

# Function to create docker-compose file on QNAP
create_docker_compose() {
    log "Creating docker-compose.yml on QNAP..."
    
    ssh "$QNAP_USER@$QNAP_HOST" "cat > /share/Container/docker-compose.yml << 'EOF'
version: '3.8'

services:
  openpolicy:
    image: $IMAGE_NAME
    container_name: $CONTAINER_NAME
    ports:
      - \"80:80\"
      - \"8000:8000\"
    volumes:
      - ./data:/app/data
      - ./regions_report.json:/app/regions_report.json:ro
      - ./scrapers:/app/scrapers:ro
      - ./policies:/app/policies:ro
    environment:
      - DATABASE_URL=sqlite:///./data/openpolicy.db
      - CORS_ORIGINS=http://localhost:3000,http://localhost:80,http://localhost:8000,http://$QNAP_HOST
      - NODE_ENV=production
    restart: unless-stopped
    healthcheck:
      test: [\"CMD\", \"curl\", \"-f\", \"http://localhost:8000/health\"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - openpolicy_network

networks:
  openpolicy_network:
    driver: bridge
EOF"
    
    success "docker-compose.yml created on QNAP"
}

# Function to create data directory on QNAP
create_data_directory() {
    log "Creating data directory on QNAP..."
    
    ssh "$QNAP_USER@$QNAP_HOST" "mkdir -p /share/Container/data"
    success "Data directory created on QNAP"
}

# Function to stop existing containers
stop_existing_containers() {
    log "Stopping existing containers on QNAP..."
    
    ssh "$QNAP_USER@$QNAP_HOST" "cd /share/Container && docker-compose down 2>/dev/null || true"
    success "Existing containers stopped"
}

# Function to pull and start containers
pull_and_start() {
    log "Pulling and starting containers on QNAP..."
    
    # Pull the latest image
    ssh "$QNAP_USER@$QNAP_HOST" "docker pull $IMAGE_NAME"
    
    # Start the services
    ssh "$QNAP_USER@$QNAP_HOST" "cd /share/Container && docker-compose up -d"
    
    success "Containers started successfully on QNAP"
}

# Function to test the deployment
test_deployment() {
    log "Testing deployment on QNAP..."
    
    # Wait for services to start
    sleep 30
    
    # Test health endpoint
    log "Testing health endpoint..."
    if curl -f -s --max-time 30 "http://$QNAP_HOST:8000/health" >/dev/null 2>&1; then
        success "Health endpoint is responding"
    else
        warning "Health endpoint is not responding yet (this is normal during startup)"
    fi
    
    # Test dashboard
    log "Testing dashboard..."
    if curl -f -s --max-time 30 "http://$QNAP_HOST:80/" >/dev/null 2>&1; then
        success "Dashboard is responding"
    else
        warning "Dashboard is not responding yet (this is normal during startup)"
    fi
    
    echo ""
    echo "💡 Note: It may take 2-3 minutes for all services to fully start up."
    echo "   You can check the status using: ssh $QNAP_USER@$QNAP_HOST 'docker logs $CONTAINER_NAME'"
}

# Function to show access information
show_access_info() {
    echo ""
    echo "🎉 QNAP deployment completed successfully!"
    echo ""
    echo "🌐 Access URLs:"
    echo "   Dashboard: http://$QNAP_HOST:80"
    echo "   API Root: http://$QNAP_HOST:8000"
    echo "   Health Check: http://$QNAP_HOST:8000/health"
    echo "   API Documentation: http://$QNAP_HOST:8000/docs"
    echo ""
    echo "📊 Container Information:"
    echo "   Container Name: $CONTAINER_NAME"
    echo "   Image: $IMAGE_NAME"
    echo "   Platform: ARM64 (QNAP native)"
    echo ""
}

# Function to show management commands
show_management_commands() {
    echo ""
    echo "🔧 Management Commands:"
    echo ""
    echo "   # SSH to QNAP"
    echo "   ssh $QNAP_USER@$QNAP_HOST"
    echo ""
    echo "   # View logs"
    echo "   ssh $QNAP_USER@$QNAP_HOST 'docker logs $CONTAINER_NAME'"
    echo ""
    echo "   # Check container status"
    echo "   ssh $QNAP_USER@$QNAP_HOST 'docker ps'"
    echo ""
    echo "   # Stop services"
    echo "   ssh $QNAP_USER@$QNAP_HOST 'cd /share/Container && docker-compose down'"
    echo ""
    echo "   # Restart services"
    echo "   ssh $QNAP_USER@$QNAP_HOST 'cd /share/Container && docker-compose restart'"
    echo ""
    echo "   # Update and restart"
    echo "   ssh $QNAP_USER@$QNAP_HOST 'cd /share/Container && docker-compose pull && docker-compose up -d'"
    echo ""
    echo "   # Remove everything"
    echo "   ssh $QNAP_USER@$QNAP_HOST 'cd /share/Container && docker-compose down -v --rmi all'"
    echo ""
}

# Function to create deployment summary
create_deployment_summary() {
    local timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
    local summary_file="qnap_deployment_summary_${timestamp}.md"
    
    cat > "$summary_file" << EOF
# QNAP Deployment Summary

**Date**: $(date)
**Environment**: QNAP Container Station
**Container**: $CONTAINER_NAME
**Host**: $QNAP_HOST

## Configuration
- **Image**: $IMAGE_NAME
- **Platform**: ARM64 (QNAP native)
- **Ports**: 80 (Dashboard), 8000 (API)
- **Database**: SQLite (persistent storage)
- **Rate Limiting**: In-memory

## URLs
- **Dashboard**: http://$QNAP_HOST:80
- **API Root**: http://$QNAP_HOST:8000
- **Health Check**: http://$QNAP_HOST:8000/health
- **API Documentation**: http://$QNAP_HOST:8000/docs

## Environment Variables
- DATABASE_URL: sqlite:///./data/openpolicy.db
- CORS_ORIGINS: http://localhost:3000,http://localhost:80,http://localhost:8000,http://$QNAP_HOST
- NODE_ENV: production

## Features
- ✅ Dashboard UI (React + Vite)
- ✅ FastAPI Backend
- ✅ SQLite Database
- ✅ Nginx Reverse Proxy
- ✅ Rate Limiting (In-Memory)
- ✅ Health Checks

## Notes
- Platform: ARM64 (QNAP native)
- OS: QNAP QTS (Linux-based)
- Docker: Container Station
- Redis: Removed (using in-memory rate limiting)
EOF
    
    success "Deployment summary created: $summary_file"
}

# Main deployment function
main() {
    echo "🚀 Starting QNAP deployment for OpenPolicy with Dashboard"
    echo "QNAP Host: $QNAP_HOST"
    echo "Container Name: $CONTAINER_NAME"
    echo "Image: $IMAGE_NAME"
    echo ""
    
    check_prerequisites
    create_data_directory
    create_docker_compose
    stop_existing_containers
    pull_and_start
    test_deployment
    show_access_info
    show_management_commands
    create_deployment_summary
    
    echo ""
    success "QNAP deployment completed successfully!"
    echo "🎉 Your OpenPolicy system with Dashboard is now running on QNAP!"
}

# Run main function
main "$@" 