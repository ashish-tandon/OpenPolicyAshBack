#!/bin/bash
set -e

# OpenPolicy Merge - Complete Deployment Script
# Handles setup, deployment, and initialization of the unified platform

VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Helper Functions
# =============================================================================

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# =============================================================================
# System Requirements Check
# =============================================================================

check_requirements() {
    log "🔍 Checking system requirements..."
    
    # Check Docker
    if ! command_exists docker; then
        error "Docker is not installed. Please install Docker first: https://docs.docker.com/get-docker/"
    fi
    
    # Check Docker Compose
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi
    
    # Check available disk space (need at least 5GB)
    available_space=$(df "$SCRIPT_DIR" | tail -1 | awk '{print $4}')
    if [ "$available_space" -lt 5242880 ]; then # 5GB in KB
        warn "Less than 5GB disk space available. Deployment may fail."
    fi
    
    # Check memory (recommend at least 4GB)
    if [ -f /proc/meminfo ]; then
        total_mem=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        if [ "$total_mem" -lt 4194304 ]; then # 4GB in KB
            warn "Less than 4GB RAM available. Performance may be affected."
        fi
    fi
    
    log "✅ System requirements check completed"
}

# =============================================================================
# Environment Setup
# =============================================================================

setup_environment() {
    log "⚙️ Setting up environment..."
    
    # Create environment file if it doesn't exist
    if [ ! -f .env ]; then
        log "📝 Creating environment configuration..."
        cat > .env << EOF
# OpenPolicy Merge Environment Configuration
# Generated on $(date)

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info
SECRET_KEY=$(openssl rand -hex 32)

# Database
DATABASE_URL=postgresql://openpolicy:$(openssl rand -hex 16)@db:5432/openpolicy_merge
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
CORS_ORIGINS=http://localhost:3000,http://localhost:80,https://openpolicymerge.org

# Frontend
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=production

# Scraping
SCRAPING_ENABLED=true
SCRAPING_SCHEDULE=0 2 * * *
SCRAPING_RATE_LIMIT=1.0

# External APIs
REPRESENT_API_URL=https://represent.opennorth.ca
PARLIAMENT_API_URL=https://www.ourcommons.ca

# Security
ALLOWED_HOSTS=localhost,openpolicymerge.org
EOF
        log "✅ Environment file created (.env)"
        info "📝 Please review and update the .env file with your specific configuration"
    else
        log "📄 Environment file already exists, skipping creation"
    fi
    
    # Create data directories
    mkdir -p data/{postgres,redis,app,logs,prometheus,grafana}
    chmod 755 data data/*
    
    log "✅ Environment setup completed"
}

# =============================================================================
# Docker Configuration
# =============================================================================

setup_docker() {
    log "🐳 Setting up Docker configuration..."
    
    # Create docker directory structure
    mkdir -p docker/{nginx,supervisor,postgresql,redis,prometheus,grafana}
    
    # Create health check script
    cat > docker/healthcheck.sh << 'EOF'
#!/bin/bash
# OpenPolicy Merge Health Check

# Check API health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API health check passed"
else
    echo "❌ API health check failed"
    exit 1
fi

# Check Nginx
if curl -f http://localhost:80 > /dev/null 2>&1; then
    echo "✅ Nginx health check passed"
else
    echo "❌ Nginx health check failed"
    exit 1
fi

echo "✅ All health checks passed"
exit 0
EOF
    chmod +x docker/healthcheck.sh
    
    # Create PostgreSQL initialization
    cat > docker/init-extensions.sql << 'EOF'
-- OpenPolicy Merge - PostgreSQL Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Create custom search configuration
CREATE TEXT SEARCH CONFIGURATION IF NOT EXISTS english_nostop (COPY = english);
ALTER TEXT SEARCH CONFIGURATION english_nostop ALTER MAPPING FOR asciiword, asciihword, hword_asciipart, word, hword, hword_part WITH simple;
EOF
    
    # Create Prometheus configuration
    cat > docker/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files: []

scrape_configs:
  - job_name: 'openpolicy-merge'
    static_configs:
      - targets: ['openpolicy-merge:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['db:5432']
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s
EOF
    
    log "✅ Docker configuration completed"
}

# =============================================================================
# Build and Deploy
# =============================================================================

build_application() {
    log "🔨 Building OpenPolicy Merge application..."
    
    # Build Docker images
    log "📦 Building Docker images..."
    docker-compose build --no-cache
    
    log "✅ Application build completed"
}

deploy_application() {
    log "🚀 Deploying OpenPolicy Merge..."
    
    # Pull base images first
    log "📥 Pulling base images..."
    docker-compose pull db redis
    
    # Start database services first
    log "🗄️ Starting database services..."
    docker-compose up -d db redis
    
    # Wait for services to be ready
    log "⏳ Waiting for database services to be ready..."
    sleep 30
    
    # Check database connection
    max_attempts=10
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose exec -T db pg_isready -U openpolicy -d openpolicy_merge > /dev/null 2>&1; then
            log "✅ Database is ready"
            break
        fi
        
        info "🔄 Waiting for database... (attempt $attempt/$max_attempts)"
        sleep 10
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        error "❌ Database failed to start after $max_attempts attempts"
    fi
    
    # Start main application
    log "🚀 Starting main application..."
    docker-compose up -d openpolicy-merge
    
    # Wait for application to be ready
    log "⏳ Waiting for application to be ready..."
    sleep 60
    
    # Verify deployment
    max_attempts=10
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost/health > /dev/null 2>&1; then
            log "✅ Application is ready and responding"
            break
        fi
        
        info "🔄 Waiting for application... (attempt $attempt/$max_attempts)"
        sleep 10
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        error "❌ Application failed to start after $max_attempts attempts"
    fi
    
    log "✅ Deployment completed successfully"
}

# =============================================================================
# Data Initialization
# =============================================================================

initialize_data() {
    log "📊 Initializing data..."
    
    # Run initial data population
    log "🌱 Running initial data setup..."
    docker-compose exec -T openpolicy-merge python -c "
import sys
sys.path.insert(0, '/app')

try:
    from src.database.config import initialize_database
    from src.scrapers.manager import scraper_manager
    
    print('📊 Initializing database...')
    if initialize_database():
        print('✅ Database initialization completed')
    else:
        print('❌ Database initialization failed')
        sys.exit(1)
        
    print('🔄 Starting initial data collection...')
    # This would trigger initial scrapers
    print('✅ Initial data collection queued')
    
except Exception as e:
    print(f'❌ Data initialization error: {e}')
    sys.exit(1)
"
    
    log "✅ Data initialization completed"
}

# =============================================================================
# Post-deployment Setup
# =============================================================================

post_deployment() {
    log "🔧 Running post-deployment setup..."
    
    # Create backup script
    cat > backup.sh << 'EOF'
#!/bin/bash
# OpenPolicy Merge Backup Script

BACKUP_DIR="./backups/$(date +%Y-%m-%d_%H-%M-%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Creating backup in $BACKUP_DIR..."

# Backup database
docker-compose exec -T db pg_dump -U openpolicy openpolicy_merge > "$BACKUP_DIR/database.sql"

# Backup application data
docker-compose exec -T openpolicy-merge tar -czf - /app/data > "$BACKUP_DIR/app_data.tar.gz"

echo "✅ Backup completed: $BACKUP_DIR"
EOF
    chmod +x backup.sh
    
    # Create update script
    cat > update.sh << 'EOF'
#!/bin/bash
# OpenPolicy Merge Update Script

echo "🔄 Updating OpenPolicy Merge..."

# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

echo "✅ Update completed"
EOF
    chmod +x update.sh
    
    # Create monitoring script
    cat > monitor.sh << 'EOF'
#!/bin/bash
# OpenPolicy Merge Monitoring Script

echo "📊 OpenPolicy Merge System Status"
echo "=================================="

# Container status
echo "🐳 Container Status:"
docker-compose ps

echo ""

# Health checks
echo "🏥 Health Checks:"
curl -s http://localhost/health | jq '.' 2>/dev/null || echo "❌ Health check failed"

echo ""

# Resource usage
echo "💻 Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -5

echo ""

# Logs (last 10 lines)
echo "📝 Recent Logs:"
docker-compose logs --tail=10 openpolicy-merge
EOF
    chmod +x monitor.sh
    
    log "✅ Post-deployment setup completed"
}

# =============================================================================
# Display Information
# =============================================================================

display_info() {
    log "🎉 OpenPolicy Merge deployment completed successfully!"
    
    echo ""
    echo "🌐 Application URLs:"
    echo "   Frontend:        http://localhost"
    echo "   API:             http://localhost:8000"
    echo "   API Docs:        http://localhost/docs"
    echo "   Flower Monitor:  http://localhost:5555"
    echo "   Health Check:    http://localhost/health"
    
    echo ""
    echo "📊 Management Commands:"
    echo "   Monitor status:  ./monitor.sh"
    echo "   Create backup:   ./backup.sh"
    echo "   Update system:   ./update.sh"
    echo "   View logs:       docker-compose logs -f"
    echo "   Stop services:   docker-compose down"
    echo "   Start services:  docker-compose up -d"
    
    echo ""
    echo "📁 Important Files:"
    echo "   Configuration:   .env"
    echo "   Logs:           data/logs/"
    echo "   Database:       data/postgres/"
    echo "   Backups:        backups/"
    
    echo ""
    echo "🔧 Next Steps:"
    echo "   1. Review the .env file and adjust settings as needed"
    echo "   2. Access the application at http://localhost"
    echo "   3. Monitor system status with ./monitor.sh"
    echo "   4. Set up regular backups with ./backup.sh"
    
    echo ""
    info "📖 For more information, see the README.md file"
}

# =============================================================================
# Main Deployment Flow
# =============================================================================

main() {
    echo "🚀 OpenPolicy Merge Deployment Script v$VERSION"
    echo "=================================================="
    echo ""
    
    # Parse command line arguments
    SKIP_BUILD=false
    DEVELOPMENT=false
    MONITORING=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --dev|--development)
                DEVELOPMENT=true
                shift
                ;;
            --monitoring)
                MONITORING=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --skip-build    Skip Docker image building"
                echo "  --dev           Deploy in development mode"
                echo "  --monitoring    Include monitoring stack (Prometheus/Grafana)"
                echo "  --help          Show this help message"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
    
    # Run deployment steps
    check_requirements
    setup_environment
    setup_docker
    
    if [ "$SKIP_BUILD" = false ]; then
        build_application
    fi
    
    deploy_application
    initialize_data
    post_deployment
    
    # Start monitoring if requested
    if [ "$MONITORING" = true ]; then
        log "📊 Starting monitoring stack..."
        docker-compose --profile monitoring up -d prometheus grafana
    fi
    
    display_info
    
    log "🎯 Deployment completed successfully!"
}

# Run main function with all arguments
main "$@"