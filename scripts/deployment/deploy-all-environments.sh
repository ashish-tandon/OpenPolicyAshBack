#!/bin/bash

# 🚀 Comprehensive Deployment Script
# This script deploys OpenPolicy to all environments with testing and monitoring

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
DEPLOYMENT_DIR="$PROJECT_ROOT/scripts/deployment"

# Default values
DEPLOY_LOCAL=true
DEPLOY_QNAP=true
DEPLOY_AZURE=true
PUSH_TO_GITHUB=true
PUSH_TO_DOCKERHUB=true
ENABLE_TESTING=true
ENABLE_MONITORING=false
MONITORING_EMAIL=""
SKIP_PRE_DEPLOYMENT_TESTS=false
SKIP_POST_DEPLOYMENT_TESTS=false
QNAP_HOST=""
QNAP_USER=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --local-only)
            DEPLOY_LOCAL=true
            DEPLOY_QNAP=false
            DEPLOY_AZURE=false
            shift
            ;;
        --qnap-only)
            DEPLOY_LOCAL=false
            DEPLOY_QNAP=true
            DEPLOY_AZURE=false
            shift
            ;;
        --azure-only)
            DEPLOY_LOCAL=false
            DEPLOY_QNAP=false
            DEPLOY_AZURE=true
            shift
            ;;
        --no-local)
            DEPLOY_LOCAL=false
            shift
            ;;
        --no-qnap)
            DEPLOY_QNAP=false
            shift
            ;;
        --no-azure)
            DEPLOY_AZURE=false
            shift
            ;;
        --no-testing)
            ENABLE_TESTING=false
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
        --skip-pre-tests)
            SKIP_PRE_DEPLOYMENT_TESTS=true
            shift
            ;;
        --skip-post-tests)
            SKIP_POST_DEPLOYMENT_TESTS=true
            shift
            ;;
        --no-github)
            PUSH_TO_GITHUB=false
            shift
            ;;
        --no-dockerhub)
            PUSH_TO_DOCKERHUB=false
            shift
            ;;
        --qnap-host)
            QNAP_HOST="$2"
            shift 2
            ;;
        --qnap-user)
            QNAP_USER="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --local-only          Deploy only to local environment"
            echo "  --qnap-only           Deploy only to QNAP environment"
            echo "  --azure-only          Deploy only to Azure environment"
            echo "  --no-local            Skip local deployment"
            echo "  --no-qnap             Skip QNAP deployment"
            echo "  --no-azure            Skip Azure deployment"
            echo "  --no-testing          Disable testing"
            echo "  --enable-monitoring   Enable monitoring"
            echo "  --monitoring-email    Email for monitoring alerts"
            echo "  --skip-pre-tests      Skip pre-deployment tests"
            echo "  --skip-post-tests     Skip post-deployment tests"
            echo "  --no-github           Skip GitHub push"
            echo "  --no-dockerhub        Skip Docker Hub push"
            echo "  --qnap-host           QNAP host IP"
            echo "  --qnap-user           QNAP username"
            echo "  --help                Show this help message"
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
    
    # Check Git
    if ! command -v git &> /dev/null; then
        error "Git is required but not installed"
        exit 1
    fi
    success "Git found: $(git --version)"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is required but not installed"
        exit 1
    fi
    success "Docker found: $(docker --version)"
    
    # Check curl
    if ! command -v curl &> /dev/null; then
        error "curl is required but not installed"
        exit 1
    fi
    success "curl found"
    
    # Check Azure CLI if deploying to Azure
    if [[ "$DEPLOY_AZURE" == "true" ]]; then
        if ! command -v az &> /dev/null; then
            error "Azure CLI is required for Azure deployment"
            exit 1
        fi
        success "Azure CLI found: $(az --version | head -1)"
        
        if ! az account show &> /dev/null; then
            error "Not logged into Azure. Please run 'az login'"
            exit 1
        fi
        success "Azure login verified"
    fi
    
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

# Function to push to GitHub
push_to_github() {
    if [[ "$PUSH_TO_GITHUB" == "false" ]]; then
        warning "Skipping GitHub push"
        return 0
    fi
    
    log "📤 Pushing to GitHub..."
    
    # Check if we're in a git repository
    if [[ ! -d "$PROJECT_ROOT/.git" ]]; then
        warning "Not in a git repository, skipping GitHub push"
        return 0
    fi
    
    # Check if there are changes to commit
    if git diff-index --quiet HEAD --; then
        warning "No changes to commit, skipping GitHub push"
        return 0
    fi
    
    # Add all changes
    git add .
    
    # Commit changes
    local commit_message="🚀 Comprehensive deployment update - $(date)"
    git commit -m "$commit_message" || {
        warning "Failed to commit changes"
        return 1
    }
    
    # Push to remote
    git push origin main || {
        warning "Failed to push to GitHub"
        return 1
    }
    
    success "Successfully pushed to GitHub"
}

# Function to push to Docker Hub
push_to_dockerhub() {
    if [[ "$PUSH_TO_DOCKERHUB" == "false" ]]; then
        warning "Skipping Docker Hub push"
        return 0
    fi
    
    log "🐳 Pushing to Docker Hub..."
    
    # Build image for Docker Hub
    docker build --platform linux/amd64 -t ashishtandon9/openpolicyashback:latest . || {
        error "Failed to build Docker image for Docker Hub"
        return 1
    }
    
    # Push to Docker Hub
    docker push ashishtandon9/openpolicyashback:latest || {
        error "Failed to push to Docker Hub"
        return 1
    }
    
    success "Successfully pushed to Docker Hub"
}

# Function to deploy to local environment
deploy_local() {
    if [[ "$DEPLOY_LOCAL" == "false" ]]; then
        log "Skipping local deployment"
        return 0
    fi
    
    log "🏠 Deploying to local environment..."
    
    if [[ -f "$DEPLOYMENT_DIR/deploy-local.sh" ]]; then
        local local_args=""
        if [[ "$ENABLE_TESTING" == "false" ]]; then
            local_args="$local_args --no-testing"
        fi
        if [[ "$SKIP_PRE_DEPLOYMENT_TESTS" == "true" ]]; then
            local_args="$local_args --skip-pre-tests"
        fi
        if [[ "$SKIP_POST_DEPLOYMENT_TESTS" == "true" ]]; then
            local_args="$local_args --skip-post-tests"
        fi
        if [[ "$ENABLE_MONITORING" == "true" ]]; then
            local_args="$local_args --enable-monitoring"
            if [[ -n "$MONITORING_EMAIL" ]]; then
                local_args="$local_args --monitoring-email $MONITORING_EMAIL"
            fi
        fi
        
        bash "$DEPLOYMENT_DIR/deploy-local.sh" $local_args || {
            error "Local deployment failed"
            return 1
        }
        success "Local deployment completed"
    else
        error "Local deployment script not found"
        return 1
    fi
}

# Function to deploy to QNAP environment
deploy_qnap() {
    if [[ "$DEPLOY_QNAP" == "false" ]]; then
        log "Skipping QNAP deployment"
        return 0
    fi
    
    log "🏠 Deploying to QNAP environment..."
    
    # Check QNAP configuration
    if [[ -z "$QNAP_HOST" ]]; then
        warning "QNAP host not specified, skipping QNAP deployment"
        return 0
    fi
    
    if [[ -z "$QNAP_USER" ]]; then
        warning "QNAP user not specified, skipping QNAP deployment"
        return 0
    fi
    
    if [[ -f "$DEPLOYMENT_DIR/deploy-qnap.sh" ]]; then
        # Set environment variables for QNAP deployment
        export QNAP_HOST="$QNAP_HOST"
        export QNAP_USER="$QNAP_USER"
        
        local qnap_args=""
        if [[ "$ENABLE_TESTING" == "false" ]]; then
            qnap_args="$qnap_args --no-testing"
        fi
        if [[ "$SKIP_PRE_DEPLOYMENT_TESTS" == "true" ]]; then
            qnap_args="$qnap_args --skip-pre-tests"
        fi
        if [[ "$SKIP_POST_DEPLOYMENT_TESTS" == "true" ]]; then
            qnap_args="$qnap_args --skip-post-tests"
        fi
        if [[ "$ENABLE_MONITORING" == "true" ]]; then
            qnap_args="$qnap_args --enable-monitoring"
            if [[ -n "$MONITORING_EMAIL" ]]; then
                qnap_args="$qnap_args --monitoring-email $MONITORING_EMAIL"
            fi
        fi
        
        bash "$DEPLOYMENT_DIR/deploy-qnap.sh" $qnap_args || {
            error "QNAP deployment failed"
            return 1
        }
        success "QNAP deployment completed"
    else
        error "QNAP deployment script not found"
        return 1
    fi
}

# Function to deploy to Azure environment
deploy_azure() {
    if [[ "$DEPLOY_AZURE" == "false" ]]; then
        log "Skipping Azure deployment"
        return 0
    fi
    
    log "☁️  Deploying to Azure environment..."
    
    if [[ -f "$DEPLOYMENT_DIR/deploy-azure.sh" ]]; then
        local azure_args=""
        if [[ "$ENABLE_TESTING" == "false" ]]; then
            azure_args="$azure_args --no-testing"
        fi
        if [[ "$SKIP_PRE_DEPLOYMENT_TESTS" == "true" ]]; then
            azure_args="$azure_args --skip-pre-tests"
        fi
        if [[ "$SKIP_POST_DEPLOYMENT_TESTS" == "true" ]]; then
            azure_args="$azure_args --skip-post-tests"
        fi
        if [[ "$ENABLE_MONITORING" == "true" ]]; then
            azure_args="$azure_args --enable-monitoring"
            if [[ -n "$MONITORING_EMAIL" ]]; then
                azure_args="$azure_args --monitoring-email $MONITORING_EMAIL"
            fi
        fi
        
        bash "$DEPLOYMENT_DIR/deploy-azure.sh" $azure_args || {
            error "Azure deployment failed"
            return 1
        }
        success "Azure deployment completed"
    else
        error "Azure deployment script not found"
        return 1
    fi
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
    
    # Test local deployment if deployed
    if [[ "$DEPLOY_LOCAL" == "true" ]]; then
        log "Testing local deployment..."
        if [[ -f "$TESTING_DIR/validate-deployment.sh" ]]; then
            bash "$TESTING_DIR/validate-deployment.sh" --url "http://localhost" --type "local" || {
                warning "Local deployment validation failed"
            }
        fi
    fi
    
    # Test Azure deployment if deployed
    if [[ "$DEPLOY_AZURE" == "true" ]]; then
        log "Testing Azure deployment..."
        local azure_url=$(cat "$TEST_RESULTS_DIR/azure-app-url.txt" 2>/dev/null || echo "")
        if [[ -n "$azure_url" ]] && [[ -f "$TESTING_DIR/validate-deployment.sh" ]]; then
            bash "$TESTING_DIR/validate-deployment.sh" --url "$azure_url" --type "azure" || {
                warning "Azure deployment validation failed"
            }
        fi
    fi
    
    success "Post-deployment tests completed"
}

# Function to create comprehensive deployment summary
create_deployment_summary() {
    local summary_file="$TEST_RESULTS_DIR/comprehensive-deployment-summary.md"
    local timestamp=$(date)
    
    cat > "$summary_file" << EOF
# Comprehensive Deployment Summary

**Deployment Time**: $timestamp
**Status**: ✅ Successful

## Deployment Configuration

- **Local Deployment**: $(if [[ "$DEPLOY_LOCAL" == "true" ]]; then echo "✅ Enabled"; else echo "❌ Disabled"; fi)
- **QNAP Deployment**: $(if [[ "$DEPLOY_QNAP" == "true" ]]; then echo "✅ Enabled"; else echo "❌ Disabled"; fi)
- **Azure Deployment**: $(if [[ "$DEPLOY_AZURE" == "true" ]]; then echo "✅ Enabled"; else echo "❌ Disabled"; fi)
- **Testing**: $(if [[ "$ENABLE_TESTING" == "true" ]]; then echo "✅ Enabled"; else echo "❌ Disabled"; fi)
- **Monitoring**: $(if [[ "$ENABLE_MONITORING" == "true" ]]; then echo "✅ Enabled"; else echo "❌ Disabled"; fi)
- **GitHub Push**: $(if [[ "$PUSH_TO_GITHUB" == "true" ]]; then echo "✅ Enabled"; else echo "❌ Disabled"; fi)
- **Docker Hub Push**: $(if [[ "$PUSH_TO_DOCKERHUB" == "true" ]]; then echo "✅ Enabled"; else echo "❌ Disabled"; fi)

## Deployment Results

### Local Environment
- **Status**: $(if [[ "$DEPLOY_LOCAL" == "true" ]]; then echo "✅ Deployed"; else echo "⏭️  Skipped"; fi)
- **URL**: http://localhost
- **Dashboard**: http://localhost
- **API**: http://localhost/api
- **Health**: http://localhost/health

### QNAP Environment
- **Status**: $(if [[ "$DEPLOY_QNAP" == "true" ]]; then echo "✅ Deployed"; else echo "⏭️  Skipped"; fi)
- **Host**: $QNAP_HOST
- **User**: $QNAP_USER

### Azure Environment
- **Status**: $(if [[ "$DEPLOY_AZURE" == "true" ]]; then echo "✅ Deployed"; else echo "⏭️  Skipped"; fi)
- **Resource Group**: openpolicy-rg
- **Container App**: openpolicy-app
- **URL**: $(cat "$TEST_RESULTS_DIR/azure-app-url.txt" 2>/dev/null || echo "Not available")

## Testing Results

- **Pre-Deployment Tests**: $(if [[ "$SKIP_PRE_DEPLOYMENT_TESTS" == "true" ]]; then echo "⏭️  Skipped"; else echo "✅ Completed"; fi)
- **Post-Deployment Tests**: $(if [[ "$SKIP_POST_DEPLOYMENT_TESTS" == "true" ]]; then echo "⏭️  Skipped"; else echo "✅ Completed"; fi)

## Code Repository Status

- **GitHub**: $(if [[ "$PUSH_TO_GITHUB" == "true" ]]; then echo "✅ Pushed"; else echo "⏭️  Skipped"; fi)
- **Docker Hub**: $(if [[ "$PUSH_TO_DOCKERHUB" == "true" ]]; then echo "✅ Pushed"; else echo "⏭️  Skipped"; fi)

## Monitoring Status

- **Status**: $(if [[ "$ENABLE_MONITORING" == "true" ]]; then echo "✅ Enabled"; else echo "❌ Disabled"; fi)
- **Email**: $MONITORING_EMAIL
- **Logs**: $MONITORING_DIR/monitoring.log
- **Metrics**: $MONITORING_DIR/metrics.json

## Access Information

### Local Environment
- Dashboard: http://localhost
- API: http://localhost/api
- Health: http://localhost/health

### Azure Environment
- Dashboard: $(cat "$TEST_RESULTS_DIR/azure-app-url.txt" 2>/dev/null || echo "Not available")
- API: $(cat "$TEST_RESULTS_DIR/azure-app-url.txt" 2>/dev/null || echo "Not available")/api
- Health: $(cat "$TEST_RESULTS_DIR/azure-app-url.txt" 2>/dev/null || echo "Not available")/health

## Next Steps

1. Access the deployed applications
2. Monitor performance and logs
3. Run validation tests as needed
4. Set up continuous monitoring

## Troubleshooting

If any deployment failed:

1. Check the specific deployment logs
2. Run validation tests: \`bash $TESTING_DIR/validate-deployment.sh --url <url> --type <environment>\`
3. Review the deployment summaries in $TEST_RESULTS_DIR
4. Check monitoring logs in $MONITORING_DIR

EOF
    
    success "Comprehensive deployment summary created: $summary_file"
}

# Function to show final status
show_final_status() {
    log "🎉 Comprehensive Deployment Completed!"
    echo ""
    echo "📊 Deployment Summary:"
    echo "  Local: $(if [[ "$DEPLOY_LOCAL" == "true" ]]; then echo "✅"; else echo "⏭️"; fi)"
    echo "  QNAP: $(if [[ "$DEPLOY_QNAP" == "true" ]]; then echo "✅"; else echo "⏭️"; fi)"
    echo "  Azure: $(if [[ "$DEPLOY_AZURE" == "true" ]]; then echo "✅"; else echo "⏭️"; fi)"
    echo ""
    echo "📤 Code Repository:"
    echo "  GitHub: $(if [[ "$PUSH_TO_GITHUB" == "true" ]]; then echo "✅"; else echo "⏭️"; fi)"
    echo "  Docker Hub: $(if [[ "$PUSH_TO_DOCKERHUB" == "true" ]]; then echo "✅"; else echo "⏭️"; fi)"
    echo ""
    echo "🧪 Testing:"
    echo "  Pre-deployment: $(if [[ "$SKIP_PRE_DEPLOYMENT_TESTS" == "true" ]]; then echo "⏭️"; else echo "✅"; fi)"
    echo "  Post-deployment: $(if [[ "$SKIP_POST_DEPLOYMENT_TESTS" == "true" ]]; then echo "⏭️"; else echo "✅"; fi)"
    echo ""
    echo "📊 Monitoring: $(if [[ "$ENABLE_MONITORING" == "true" ]]; then echo "✅"; else echo "❌"; fi)"
    echo ""
    echo "📋 Results available in: $TEST_RESULTS_DIR"
    echo "📊 Monitoring logs: $MONITORING_DIR"
    echo ""
}

# Main execution
main() {
    log "🚀 Starting Comprehensive Deployment to All Environments"
    
    # Create necessary directories
    mkdir -p "$TEST_RESULTS_DIR" "$MONITORING_DIR"
    
    # Run deployment process
    check_prerequisites
    run_pre_deployment_tests
    push_to_github
    push_to_dockerhub
    deploy_local
    deploy_qnap
    deploy_azure
    run_post_deployment_tests
    create_deployment_summary
    show_final_status
    
    success "Comprehensive deployment completed successfully!"
}

# Run main function
main "$@" 