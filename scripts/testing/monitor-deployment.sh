#!/bin/bash

# 📊 Deployment Monitoring Script
# This script provides continuous monitoring of the deployed application

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
MONITORING_DIR="$PROJECT_ROOT/monitoring"
LOG_FILE="$MONITORING_DIR/monitoring.log"
METRICS_FILE="$MONITORING_DIR/metrics.json"
ALERTS_FILE="$MONITORING_DIR/alerts.log"

# Default values
DEPLOYMENT_URL=""
DEPLOYMENT_TYPE=""
MONITORING_INTERVAL=60
ALERT_EMAIL=""
ENABLE_ALERTS=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            DEPLOYMENT_URL="$2"
            shift 2
            ;;
        --type)
            DEPLOYMENT_TYPE="$2"
            shift 2
            ;;
        --interval)
            MONITORING_INTERVAL="$2"
            shift 2
            ;;
        --email)
            ALERT_EMAIL="$2"
            ENABLE_ALERTS=true
            shift 2
            ;;
        --help)
            echo "Usage: $0 --url <deployment-url> --type <local|qnap|azure> [--interval <seconds>] [--email <email>]"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$DEPLOYMENT_URL" ]]; then
    error "Deployment URL is required. Use --url parameter."
    exit 1
fi

if [[ -z "$DEPLOYMENT_TYPE" ]]; then
    error "Deployment type is required. Use --type parameter (local|qnap|azure)."
    exit 1
fi

# Create monitoring directory
mkdir -p "$MONITORING_DIR"

# Initialize metrics file
if [[ ! -f "$METRICS_FILE" ]]; then
    cat > "$METRICS_FILE" << EOF
{
    "start_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "deployment_url": "$DEPLOYMENT_URL",
    "deployment_type": "$DEPLOYMENT_TYPE",
    "checks": [],
    "alerts": [],
    "summary": {
        "total_checks": 0,
        "successful_checks": 0,
        "failed_checks": 0,
        "uptime_percentage": 0
    }
}
EOF
fi

# Function to send alert
send_alert() {
    local message="$1"
    local severity="$2"
    
    if [[ "$ENABLE_ALERTS" == "true" && -n "$ALERT_EMAIL" ]]; then
        echo "[$(date)] $severity: $message" >> "$ALERTS_FILE"
        
        # Send email alert (requires mail command)
        if command -v mail &> /dev/null; then
            echo "$message" | mail -s "OpenPolicy Alert: $severity" "$ALERT_EMAIL" || true
        fi
    fi
    
    case "$severity" in
        "CRITICAL")
            error "$message"
            ;;
        "WARNING")
            warning "$message"
            ;;
        "INFO")
            log "$message"
            ;;
    esac
}

# Function to update metrics
update_metrics() {
    local check_type="$1"
    local status="$2"
    local response_time="$3"
    local details="$4"
    
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local check_data="{\"timestamp\": \"$timestamp\", \"type\": \"$check_type\", \"status\": \"$status\", \"response_time\": $response_time, \"details\": \"$details\"}"
    
    # Update metrics file using jq if available
    if command -v jq &> /dev/null; then
        jq --argjson check "$check_data" '.checks += [$check]' "$METRICS_FILE" > "$METRICS_FILE.tmp" && mv "$METRICS_FILE.tmp" "$METRICS_FILE"
    else
        # Simple append if jq is not available
        echo "$check_data" >> "$METRICS_FILE"
    fi
}

# Function to check health endpoint
check_health() {
    local start_time=$(date +%s%N)
    local response
    
    response=$(curl -f -s "$DEPLOYMENT_URL/health" 2>/dev/null) || {
        local end_time=$(date +%s%N)
        local response_time=$(( (end_time - start_time) / 1000000 ))
        update_metrics "health" "failed" "$response_time" "Health endpoint unreachable"
        send_alert "Health endpoint is down" "CRITICAL"
        return 1
    }
    
    local end_time=$(date +%s%N)
    local response_time=$(( (end_time - start_time) / 1000000 ))
    
    if echo "$response" | grep -q "healthy"; then
        update_metrics "health" "success" "$response_time" "Healthy"
        if [[ $response_time -gt 2000 ]]; then
            send_alert "Health endpoint response time: ${response_time}ms (slow)" "WARNING"
        fi
        return 0
    else
        update_metrics "health" "failed" "$response_time" "Unhealthy response"
        send_alert "Health endpoint returned unhealthy status" "CRITICAL"
        return 1
    fi
}

# Function to check API endpoints
check_api_endpoints() {
    local endpoints=("stats" "jurisdictions" "representatives")
    local failed_endpoints=()
    
    for endpoint in "${endpoints[@]}"; do
        local start_time=$(date +%s%N)
        local url="$DEPLOYMENT_URL/$endpoint"
        
        if curl -f -s "$url" >/dev/null 2>&1; then
            local end_time=$(date +%s%N)
            local response_time=$(( (end_time - start_time) / 1000000 ))
            update_metrics "api_$endpoint" "success" "$response_time" "Working"
            
            if [[ $response_time -gt 3000 ]]; then
                send_alert "API endpoint $endpoint response time: ${response_time}ms (slow)" "WARNING"
            fi
        else
            local end_time=$(date +%s%N)
            local response_time=$(( (end_time - start_time) / 1000000 ))
            update_metrics "api_$endpoint" "failed" "$response_time" "Failed"
            failed_endpoints+=("$endpoint")
        fi
    done
    
    if [[ ${#failed_endpoints[@]} -gt 0 ]]; then
        send_alert "Failed API endpoints: ${failed_endpoints[*]}" "CRITICAL"
        return 1
    fi
    
    return 0
}

# Function to check dashboard
check_dashboard() {
    local start_time=$(date +%s%N)
    local response
    
    response=$(curl -f -s "$DEPLOYMENT_URL" 2>/dev/null) || {
        local end_time=$(date +%s%N)
        local response_time=$(( (end_time - start_time) / 1000000 ))
        update_metrics "dashboard" "failed" "$response_time" "Dashboard unreachable"
        send_alert "Dashboard is down" "CRITICAL"
        return 1
    }
    
    local end_time=$(date +%s%N)
    local response_time=$(( (end_time - start_time) / 1000000 ))
    
    if echo "$response" | grep -q "OpenPolicy Dashboard"; then
        update_metrics "dashboard" "success" "$response_time" "Loading correctly"
        if [[ $response_time -gt 5000 ]]; then
            send_alert "Dashboard load time: ${response_time}ms (slow)" "WARNING"
        fi
        return 0
    else
        update_metrics "dashboard" "failed" "$response_time" "Unexpected content"
        send_alert "Dashboard returned unexpected content" "CRITICAL"
        return 1
    fi
}

# Function to check database connectivity
check_database() {
    local start_time=$(date +%s%N)
    local response
    
    response=$(curl -f -s "$DEPLOYMENT_URL/stats" 2>/dev/null) || {
        local end_time=$(date +%s%N)
        local response_time=$(( (end_time - start_time) / 1000000 ))
        update_metrics "database" "failed" "$response_time" "Database unreachable"
        send_alert "Database connectivity failed" "CRITICAL"
        return 1
    }
    
    local end_time=$(date +%s%N)
    local response_time=$(( (end_time - start_time) / 1000000 ))
    
    if echo "$response" | grep -q "total_jurisdictions\|total_representatives\|total_bills"; then
        update_metrics "database" "success" "$response_time" "Connected"
        return 0
    else
        update_metrics "database" "failed" "$response_time" "Invalid response"
        send_alert "Database returned invalid response" "CRITICAL"
        return 1
    fi
}

# Function to check environment-specific metrics
check_environment_metrics() {
    case "$DEPLOYMENT_TYPE" in
        "local")
            # Check Docker container status
            if ! docker ps | grep -q "openpolicy"; then
                send_alert "Local container is not running" "CRITICAL"
                update_metrics "container" "failed" 0 "Container not running"
            else
                update_metrics "container" "success" 0 "Container running"
            fi
            ;;
            
        "qnap")
            # Check QNAP connectivity if host is configured
            if [[ -n "$QNAP_HOST" ]]; then
                if ping -c 1 "$QNAP_HOST" >/dev/null 2>&1; then
                    update_metrics "qnap_connectivity" "success" 0 "QNAP reachable"
                else
                    send_alert "QNAP host is not reachable" "WARNING"
                    update_metrics "qnap_connectivity" "failed" 0 "QNAP unreachable"
                fi
            fi
            ;;
            
        "azure")
            # Check Azure Container Apps status
            if command -v az &> /dev/null; then
                local app_status=$(az containerapp show --resource-group openpolicy-rg --name openpolicy-app --query "properties.runningStatus" --output tsv 2>/dev/null || echo "unknown")
                if [[ "$app_status" == "Running" ]]; then
                    update_metrics "azure_status" "success" 0 "Container App running"
                else
                    send_alert "Azure Container App status: $app_status" "CRITICAL"
                    update_metrics "azure_status" "failed" 0 "Container App not running"
                fi
            fi
            ;;
    esac
}

# Function to generate monitoring report
generate_monitoring_report() {
    local report_file="$MONITORING_DIR/monitoring-report.md"
    local timestamp=$(date)
    
    # Calculate summary statistics
    local total_checks=0
    local successful_checks=0
    local failed_checks=0
    
    if command -v jq &> /dev/null; then
        total_checks=$(jq '.checks | length' "$METRICS_FILE" 2>/dev/null || echo "0")
        successful_checks=$(jq '.checks | map(select(.status == "success")) | length' "$METRICS_FILE" 2>/dev/null || echo "0")
        failed_checks=$(jq '.checks | map(select(.status == "failed")) | length' "$METRICS_FILE" 2>/dev/null || echo "0")
    fi
    
    local uptime_percentage=0
    if [[ $total_checks -gt 0 ]]; then
        uptime_percentage=$(( (successful_checks * 100) / total_checks ))
    fi
    
    cat > "$report_file" << EOF
# Monitoring Report

**Generated**: $timestamp
**Deployment URL**: $DEPLOYMENT_URL
**Deployment Type**: $DEPLOYMENT_TYPE
**Monitoring Duration**: $(($(date +%s) - $(date -d "$(jq -r '.start_time' "$METRICS_FILE" 2>/dev/null || echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)")" +%s 2>/dev/null || echo "$(date +%s)"))) seconds

## Summary

- **Total Checks**: $total_checks
- **Successful Checks**: $successful_checks
- **Failed Checks**: $failed_checks
- **Uptime Percentage**: ${uptime_percentage}%

## Recent Alerts

$(if [[ -f "$ALERTS_FILE" ]]; then tail -10 "$ALERTS_FILE"; else echo "No alerts recorded"; fi)

## Performance Metrics

### Response Times (Last 10 checks)
$(if command -v jq &> /dev/null; then
    jq -r '.checks[-10:] | .[] | "\(.type): \(.response_time)ms (\(.status))"' "$METRICS_FILE" 2>/dev/null || echo "No metrics available"
else
    echo "Metrics available in $METRICS_FILE"
fi)

## Recommendations

1. Monitor uptime percentage
2. Review failed checks
3. Investigate slow response times
4. Set up automated alerts

EOF
    
    log "Monitoring report generated: $report_file"
}

# Function to cleanup old metrics
cleanup_old_metrics() {
    # Keep only last 1000 checks to prevent file from growing too large
    if command -v jq &> /dev/null; then
        jq '.checks = (.checks[-1000:])' "$METRICS_FILE" > "$METRICS_FILE.tmp" && mv "$METRICS_FILE.tmp" "$METRICS_FILE" 2>/dev/null || true
    fi
}

# Function to run monitoring cycle
run_monitoring_cycle() {
    local cycle_start=$(date +%s)
    
    log "🔄 Starting monitoring cycle..."
    
    # Run all checks
    check_health
    check_api_endpoints
    check_dashboard
    check_database
    check_environment_metrics
    
    # Generate report every 10 cycles
    local cycle_count=$((cycle_start / MONITORING_INTERVAL))
    if [[ $((cycle_count % 10)) -eq 0 ]]; then
        generate_monitoring_report
        cleanup_old_metrics
    fi
    
    local cycle_end=$(date +%s)
    local cycle_duration=$((cycle_end - cycle_start))
    
    log "✅ Monitoring cycle completed in ${cycle_duration}s"
}

# Main monitoring loop
main() {
    log "🚀 Starting Continuous Monitoring"
    log "Deployment URL: $DEPLOYMENT_URL"
    log "Deployment Type: $DEPLOYMENT_TYPE"
    log "Monitoring Interval: ${MONITORING_INTERVAL}s"
    log "Alerts Enabled: $ENABLE_ALERTS"
    
    if [[ "$ENABLE_ALERTS" == "true" ]]; then
        log "Alert Email: $ALERT_EMAIL"
    fi
    
    # Send startup alert
    send_alert "Monitoring started for $DEPLOYMENT_TYPE deployment" "INFO"
    
    # Main monitoring loop
    while true; do
        run_monitoring_cycle
        
        # Wait for next cycle
        sleep "$MONITORING_INTERVAL"
    done
}

# Handle script interruption
trap 'log "🛑 Monitoring stopped by user"; send_alert "Monitoring stopped" "INFO"; exit 0' INT TERM

# Run main function
main "$@" 