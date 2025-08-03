#!/bin/bash

# OpenPolicy System Monitoring Script
# Monitors the health and status of all services

set -e

# Configuration
QNAP_HOST="ashishsnas.myqnapcloud.com"
CONTAINER_NAME="openpolicy_single"
LOG_FILE="system_monitor.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a ${LOG_FILE}
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a ${LOG_FILE}
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a ${LOG_FILE}
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a ${LOG_FILE}
}

# Function to check service health
check_service_health() {
    local service_name=$1
    local url=$2
    local description=$3
    
    log "Checking $service_name..."
    
    if curl -f -s --max-time 10 "$url" >/dev/null 2>&1; then
        success "$service_name is healthy - $description"
        return 0
    else
        error "$service_name is not responding - $description"
        return 1
    fi
}

# Function to check container status
check_container_status() {
    log "Checking container status on QNAP..."
    
    # Check if we can SSH to QNAP
    if ssh -o ConnectTimeout=10 admin@${QNAP_HOST} "docker ps | grep ${CONTAINER_NAME}" >/dev/null 2>&1; then
        success "Container ${CONTAINER_NAME} is running on QNAP"
        
        # Get container status
        CONTAINER_STATUS=$(ssh admin@${QNAP_HOST} "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep ${CONTAINER_NAME}")
        log "Container status: $CONTAINER_STATUS"
        
        return 0
    else
        error "Container ${CONTAINER_NAME} is not running on QNAP"
        return 1
    fi
}

# Function to check system resources
check_system_resources() {
    log "Checking system resources on QNAP..."
    
    # Get system info
    if ssh -o ConnectTimeout=10 admin@${QNAP_HOST} "df -h /" >/dev/null 2>&1; then
        DISK_USAGE=$(ssh admin@${QNAP_HOST} "df -h / | tail -1 | awk '{print \$5}'")
        MEMORY_USAGE=$(ssh admin@${QNAP_HOST} "free -h | grep Mem | awk '{print \$3}'")
        
        log "Disk usage: $DISK_USAGE"
        log "Memory usage: $MEMORY_USAGE"
        
        success "System resources check completed"
    else
        warning "Could not check system resources on QNAP"
    fi
}

# Function to check logs
check_logs() {
    log "Checking recent logs..."
    
    # Get recent container logs
    if ssh -o ConnectTimeout=10 admin@${QNAP_HOST} "docker logs --tail 20 ${CONTAINER_NAME}" >/dev/null 2>&1; then
        RECENT_LOGS=$(ssh admin@${QNAP_HOST} "docker logs --tail 10 ${CONTAINER_NAME}")
        log "Recent logs:"
        echo "$RECENT_LOGS" | while IFS= read -r line; do
            log "  $line"
        done
    else
        warning "Could not retrieve container logs"
    fi
}

# Function to check database connectivity
check_database() {
    log "Checking database connectivity..."
    
    # Test database connection through API
    if curl -f -s --max-time 10 "https://${QNAP_HOST}/api/stats" >/dev/null 2>&1; then
        success "Database is accessible through API"
        
        # Get stats
        STATS=$(curl -s "https://${QNAP_HOST}/api/stats")
        log "Database stats: $STATS"
    else
        error "Database is not accessible through API"
    fi
}

# Function to check all endpoints
check_all_endpoints() {
    log "Checking all endpoints..."
    
    local all_healthy=true
    
    # Check main dashboard
    if ! check_service_health "Dashboard" "https://${QNAP_HOST}/" "Main web interface"; then
        all_healthy=false
    fi
    
    # Check API health
    if ! check_service_health "API Health" "https://${QNAP_HOST}/health" "API health endpoint"; then
        all_healthy=false
    fi
    
    # Check API docs
    if ! check_service_health "API Docs" "https://${QNAP_HOST}/api/docs" "API documentation"; then
        all_healthy=false
    fi
    
    # Check GraphQL
    if ! check_service_health "GraphQL" "https://${QNAP_HOST}/graphql" "GraphQL endpoint"; then
        all_healthy=false
    fi
    
    # Check Flower monitor
    if ! check_service_health "Flower Monitor" "https://${QNAP_HOST}:5555" "Celery task monitor"; then
        all_healthy=false
    fi
    
    if [ "$all_healthy" = true ]; then
        success "All endpoints are healthy"
    else
        error "Some endpoints are not responding"
    fi
}

# Function to create status report
create_status_report() {
    log "Creating status report..."
    
    TIMESTAMP=$(date +'%Y-%m-%d %H:%M:%S')
    
    cat > STATUS_REPORT_${TIMESTAMP// /_}.md << EOF
# OpenPolicy System Status Report

**Report Date:** ${TIMESTAMP}
**System:** QNAP NAS (${QNAP_HOST})

## System Overview

### Container Status
- **Container Name:** ${CONTAINER_NAME}
- **Status:** $(ssh admin@${QNAP_HOST} "docker ps --format '{{.Status}}' | grep ${CONTAINER_NAME}" 2>/dev/null || echo "Unknown")

### Endpoint Status
- **Dashboard:** $(curl -f -s "https://${QNAP_HOST}/" >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Unhealthy")
- **API Health:** $(curl -f -s "https://${QNAP_HOST}/health" >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Unhealthy")
- **API Docs:** $(curl -f -s "https://${QNAP_HOST}/api/docs" >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Unhealthy")
- **GraphQL:** $(curl -f -s "https://${QNAP_HOST}/graphql" >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Unhealthy")
- **Flower Monitor:** $(curl -f -s "https://${QNAP_HOST}:5555" >/dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Unhealthy")

### Database Status
- **Connectivity:** $(curl -f -s "https://${QNAP_HOST}/api/stats" >/dev/null 2>&1 && echo "✅ Connected" || echo "❌ Disconnected")

## Recent Logs
\`\`\`
$(ssh admin@${QNAP_HOST} "docker logs --tail 20 ${CONTAINER_NAME}" 2>/dev/null || echo "Could not retrieve logs")
\`\`\`

## System Resources
$(ssh admin@${QNAP_HOST} "df -h / | tail -1" 2>/dev/null || echo "Could not retrieve disk usage")

## Recommendations

1. Monitor logs for any errors
2. Check system resources regularly
3. Verify all endpoints are accessible
4. Ensure database connectivity

EOF

    success "Status report created: STATUS_REPORT_${TIMESTAMP// /_}.md"
}

# Function to restart services if needed
restart_services() {
    log "Checking if services need restart..."
    
    # Check if any critical services are down
    local needs_restart=false
    
    if ! curl -f -s --max-time 10 "https://${QNAP_HOST}/health" >/dev/null 2>&1; then
        warning "API health check failed - considering restart"
        needs_restart=true
    fi
    
    if ! curl -f -s --max-time 10 "https://${QNAP_HOST}/" >/dev/null 2>&1; then
        warning "Dashboard is not responding - considering restart"
        needs_restart=true
    fi
    
    if [ "$needs_restart" = true ]; then
        log "Restarting services..."
        
        if ssh admin@${QNAP_HOST} "docker restart ${CONTAINER_NAME}"; then
            success "Services restarted successfully"
            log "Waiting for services to come back online..."
            sleep 30
            
            # Check if services are back
            if curl -f -s --max-time 10 "https://${QNAP_HOST}/health" >/dev/null 2>&1; then
                success "Services are back online"
            else
                error "Services failed to come back online after restart"
            fi
        else
            error "Failed to restart services"
        fi
    else
        success "All services are healthy - no restart needed"
    fi
}

# Main monitoring function
main() {
    log "🔍 Starting OpenPolicy System Monitoring"
    
    # Check container status
    check_container_status
    
    # Check system resources
    check_system_resources
    
    # Check all endpoints
    check_all_endpoints
    
    # Check database
    check_database
    
    # Check logs
    check_logs
    
    # Restart services if needed
    restart_services
    
    # Create status report
    create_status_report
    
    log "📊 Monitoring completed"
}

# Run main function
main "$@" 