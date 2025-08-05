#!/bin/bash

# Test QNAP Deployment Script
# Tests and monitors the OpenPolicy system deployment on QNAP

set -e

# Configuration
QNAP_HOST="192.168.2.152"
QNAP_PORT="22"
QNAP_USER="ashish101"
QNAP_PASS="Pergola@41"

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

# Function to test QNAP connectivity
test_qnap_connectivity() {
    log "Testing QNAP connectivity..."
    
    if ping -c 1 ${QNAP_HOST} >/dev/null 2>&1; then
        success "QNAP is reachable"
        return 0
    else
        error "QNAP is not reachable"
        return 1
    fi
}

# Function to test Container Station web interface
test_container_station_web() {
    log "Testing Container Station web interface..."
    
    if curl -f -s --max-time 10 http://${QNAP_HOST}:8080/container-station/ >/dev/null 2>&1; then
        success "Container Station web interface is accessible"
        return 0
    else
        warning "Container Station web interface is not accessible"
        return 1
    fi
}

# Function to test main application endpoints
test_application_endpoints() {
    log "Testing application endpoints..."
    
    local endpoints=(
        "http://${QNAP_HOST}:8000/health"
        "http://${QNAP_HOST}:3000"
        "http://${QNAP_HOST}"
        "http://${QNAP_HOST}:5555"
    )
    
    local endpoint_names=(
        "API Health"
        "Dashboard"
        "Main Entry Point"
        "Flower Monitor"
    )
    
    for i in "${!endpoints[@]}"; do
        log "Testing ${endpoint_names[$i]}..."
        if curl -f -s --max-time 10 "${endpoints[$i]}" >/dev/null 2>&1; then
            success "${endpoint_names[$i]} is responding"
        else
            warning "${endpoint_names[$i]} is not responding"
        fi
    done
}

# Function to check container status via SSH
check_container_status() {
    log "Checking container status via SSH..."
    
    if command -v sshpass &> /dev/null; then
        if sshpass -p "${QNAP_PASS}" ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "docker ps | grep openpolicy_single" 2>/dev/null; then
            success "Container is running on QNAP"
            return 0
        else
            warning "Container is not running on QNAP"
            return 1
        fi
    else
        warning "sshpass not available, cannot check container status via SSH"
        return 1
    fi
}

# Function to show container logs via SSH
show_container_logs() {
    log "Showing recent container logs..."
    
    if command -v sshpass &> /dev/null; then
        sshpass -p "${QNAP_PASS}" ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "docker logs --tail 10 openpolicy_single" 2>/dev/null || {
            warning "Could not retrieve container logs"
        }
    else
        warning "sshpass not available, cannot retrieve container logs"
    fi
}

# Function to show access URLs
show_access_urls() {
    log "Access URLs:"
    echo ""
    echo "🌐 Local Network Access:"
    echo "   Main Dashboard: http://${QNAP_HOST}"
    echo "   API Documentation: http://${QNAP_HOST}:8000/docs"
    echo "   Health Check: http://${QNAP_HOST}:8000/health"
    echo "   Flower Monitor: http://${QNAP_HOST}:5555"
    echo ""
    echo "🌐 Domain Access (if available):"
    echo "   Main Dashboard: https://ashishsnas.myqnapcloud.com"
    echo "   API Documentation: https://ashishsnas.myqnapcloud.com/api/docs"
    echo "   Health Check: https://ashishsnas.myqnapcloud.com/health"
    echo ""
    echo "📱 Container Station Management:"
    echo "   Container Station UI: http://${QNAP_HOST}:8080"
    echo "   Container Management: http://${QNAP_HOST}:8080/container-station/"
}

# Function to create status report
create_status_report() {
    log "Creating status report..."
    
    TIMESTAMP=$(date +'%Y-%m-%d %H:%M:%S')
    
    cat > QNAP_STATUS_REPORT_${TIMESTAMP// /_}.md << EOF
# QNAP Deployment Status Report

**Report Date:** ${TIMESTAMP}
**QNAP Host:** ${QNAP_HOST}

## Connectivity Tests

### QNAP Reachability
- Status: $(ping -c 1 ${QNAP_HOST} >/dev/null 2>&1 && echo "✅ Reachable" || echo "❌ Not Reachable")

### Container Station Web Interface
- Status: $(curl -f -s --max-time 10 http://${QNAP_HOST}:8080/container-station/ >/dev/null 2>&1 && echo "✅ Accessible" || echo "❌ Not Accessible")

## Application Endpoints

### API Health
- URL: http://${QNAP_HOST}:8000/health
- Status: $(curl -f -s --max-time 10 http://${QNAP_HOST}:8000/health >/dev/null 2>&1 && echo "✅ Responding" || echo "❌ Not Responding")

### Dashboard
- URL: http://${QNAP_HOST}:3000
- Status: $(curl -f -s --max-time 10 http://${QNAP_HOST}:3000 >/dev/null 2>&1 && echo "✅ Responding" || echo "❌ Not Responding")

### Main Entry Point
- URL: http://${QNAP_HOST}
- Status: $(curl -f -s --max-time 10 http://${QNAP_HOST} >/dev/null 2>&1 && echo "✅ Responding" || echo "❌ Not Responding")

### Flower Monitor
- URL: http://${QNAP_HOST}:5555
- Status: $(curl -f -s --max-time 10 http://${QNAP_HOST}:5555 >/dev/null 2>&1 && echo "✅ Responding" || echo "❌ Not Responding")

## Container Status

$(if command -v sshpass &> /dev/null; then
    sshpass -p "${QNAP_PASS}" ssh -o ConnectTimeout=10 -p ${QNAP_PORT} ${QNAP_USER}@${QNAP_HOST} "docker ps | grep openpolicy_single" 2>/dev/null && echo "✅ Container is running" || echo "❌ Container is not running"
else
    echo "⚠️ Cannot check container status (sshpass not available)"
fi)

## Access URLs

### Local Network Access
- Main Dashboard: http://${QNAP_HOST}
- API Documentation: http://${QNAP_HOST}:8000/docs
- Health Check: http://${QNAP_HOST}:8000/health
- Flower Monitor: http://${QNAP_HOST}:5555

### Domain Access
- Main Dashboard: https://ashishsnas.myqnapcloud.com
- API Documentation: https://ashishsnas.myqnapcloud.com/api/docs
- Health Check: https://ashishsnas.myqnapcloud.com/health

### Container Station Management
- Container Station UI: http://${QNAP_HOST}:8080
- Container Management: http://${QNAP_HOST}:8080/container-station/

## Next Steps

1. If endpoints are not responding, check Container Station for container status
2. Review container logs for any errors
3. Ensure all required ports are available
4. Verify the Docker image exists and is accessible

EOF

    success "Status report created: QNAP_STATUS_REPORT_${TIMESTAMP// /_}.md"
}

# Main function
main() {
    log "🔍 Starting QNAP Deployment Testing"
    log "QNAP Host: ${QNAP_HOST}"
    
    # Test QNAP connectivity
    if test_qnap_connectivity; then
        # Test Container Station web interface
        test_container_station_web
        
        # Test application endpoints
        test_application_endpoints
        
        # Check container status
        check_container_status
        
        # Show container logs
        show_container_logs
        
        # Show access URLs
        show_access_urls
        
        # Create status report
        create_status_report
        
        log "🎉 QNAP deployment testing completed!"
        log "Check the status report for detailed results"
    else
        error "Cannot test deployment - QNAP is not reachable"
        log "Please ensure QNAP is powered on and accessible on the network"
    fi
}

# Run main function
main "$@" 