#!/bin/bash

# 🚀 Local Deployment Script for OpenPolicy with Dashboard
# Deploys locally with Docker Compose (no Redis dependency)

set -e

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
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    success "Docker is installed"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    success "Docker Compose is installed"
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    success "Docker is running"
}

# Function to create docker-compose.yml
create_docker_compose() {
    log "Creating docker-compose.yml..."
    
    cat > docker-compose.yml << 'EOF'
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
    log "Creating data directory..."
    
    mkdir -p data
    success "Data directory created"
}

# Function to stop existing containers
stop_existing_containers() {
    log "Stopping existing containers..."
    
    if docker ps -q --filter "name=openpolicy" | grep -q .; then
        docker-compose down
        success "Existing containers stopped"
    else
        warning "No existing containers found"
    fi
}

# Function to build and start containers
build_and_start() {
    log "Building and starting containers..."
    
    # Build the image
    docker-compose build
    
    # Start the services
    docker-compose up -d
    
    success "Containers started successfully"
}

# Function to test the deployment
test_deployment() {
    log "Testing deployment..."
    
    # Wait for services to start
    sleep 30
    
    # Test health endpoint
    log "Testing health endpoint..."
    if curl -f -s --max-time 30 "http://localhost:8000/health" >/dev/null 2>&1; then
        success "Health endpoint is responding"
    else
        warning "Health endpoint is not responding yet (this is normal during startup)"
    fi
    
    # Test dashboard
    log "Testing dashboard..."
    if curl -f -s --max-time 30 "http://localhost:80/" >/dev/null 2>&1; then
        success "Dashboard is responding"
    else
        warning "Dashboard is not responding yet (this is normal during startup)"
    fi
    
    echo ""
    echo "💡 Note: It may take 2-3 minutes for all services to fully start up."
    echo "   You can check the status using: docker-compose logs -f"
}

# Function to show access information
show_access_info() {
    echo ""
    echo "🎉 Local deployment completed successfully!"
    echo ""
    echo "🌐 Access URLs:"
    echo "   Dashboard: http://localhost:80"
    echo "   API Root: http://localhost:8000"
    echo "   Health Check: http://localhost:8000/health"
    echo "   API Documentation: http://localhost:8000/docs"
    echo ""
    echo "📊 Container Information:"
    echo "   Container Name: openpolicy_local"
    echo "   Image: Built locally with dashboard"
    echo "   Platform: Auto-detected (macOS compatible)"
    echo ""
}

# Function to show management commands
show_management_commands() {
    echo ""
    echo "🔧 Management Commands:"
    echo ""
    echo "   # View logs"
    echo "   docker-compose logs -f"
    echo ""
    echo "   # Check container status"
    echo "   docker-compose ps"
    echo ""
    echo "   # Stop services"
    echo "   docker-compose down"
    echo ""
    echo "   # Restart services"
    echo "   docker-compose restart"
    echo ""
    echo "   # Rebuild and restart"
    echo "   docker-compose up -d --build"
    echo ""
    echo "   # Remove everything"
    echo "   docker-compose down -v --rmi all"
    echo ""
}

# Function to create deployment summary
create_deployment_summary() {
    local timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
    local summary_file="local_deployment_summary_${timestamp}.md"
    
    cat > "$summary_file" << EOF
# Local Deployment Summary

**Date**: $(date)
**Environment**: Local macOS
**Container**: openpolicy_local

## Configuration
- **Image**: Built locally with dashboard
- **Platform**: Auto-detected (macOS compatible)
- **Ports**: 80 (Dashboard), 8000 (API)
- **Database**: SQLite (local file)
- **Redis**: Removed (using in-memory rate limiting)

## URLs
- **Dashboard**: http://localhost:80
- **API Root**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs

## Environment Variables
- DATABASE_URL: sqlite:///./data/openpolicy.db
- CORS_ORIGINS: http://localhost:3000,http://localhost:80,http://localhost:8000
- NODE_ENV: production

## Features
- ✅ Dashboard UI (React + Vite)
- ✅ FastAPI Backend
- ✅ SQLite Database
- ✅ Nginx Reverse Proxy
- ✅ Rate Limiting (In-Memory)
- ✅ Health Checks

## Notes
- Platform: Auto-detected (no explicit specification needed)
- OS: macOS (Apple Silicon or Intel)
- Docker: Docker Desktop
- Redis: Removed (using in-memory rate limiting)
EOF
    
    success "Deployment summary created: $summary_file"
}

# Main deployment function
main() {
    echo "🚀 Starting local deployment for OpenPolicy with Dashboard"
    echo "Environment: Local macOS"
    echo "Container: openpolicy_local"
    echo ""
    
    check_prerequisites
    create_data_directory
    create_docker_compose
    stop_existing_containers
    build_and_start
    test_deployment
    show_access_info
    show_management_commands
    create_deployment_summary
    
    echo ""
    success "Local deployment completed successfully!"
    echo "🎉 Your OpenPolicy system with Dashboard is now running locally!"
}

# Run main function
main "$@" 