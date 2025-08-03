#!/bin/bash

# OpenPolicy PostgreSQL Deployment Script
# This script deploys the complete OpenPolicy system with PostgreSQL database

set -e

echo "🚀 OpenPolicy PostgreSQL Deployment"
echo "=================================="
echo ""

# Configuration
QNAP_HOST="192.168.2.152"
QNAP_USER="ashish101"
DEPLOY_PATH="/share/Container/openpolicy-postgresql"

echo "📋 Configuration:"
echo "=================="
echo "  • QNAP Host: $QNAP_HOST"
echo "  • QNAP User: $QNAP_USER"
echo "  • Deploy Path: $DEPLOY_PATH"
echo ""

# Step 1: Stop and remove existing containers
echo "🛑 Step 1: Cleaning up existing containers..."
ssh $QNAP_USER@$QNAP_HOST '
    # Stop and remove existing containers
    /share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker stop openpolicy_all_in_one 2>/dev/null || true
    /share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker rm openpolicy_all_in_one 2>/dev/null || true
    
    # Remove old images
    /share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker rmi ashishtandon9/openpolicyashback:all-in-one 2>/dev/null || true
    
    echo "  ✅ Cleanup completed"
'

# Step 2: Create deployment directory
echo ""
echo "📁 Step 2: Creating deployment directory..."
ssh $QNAP_USER@$QNAP_HOST "
    mkdir -p $DEPLOY_PATH
    mkdir -p $DEPLOY_PATH/dashboard
    mkdir -p $DEPLOY_PATH/scrapers
    echo '  ✅ Directory structure created'
"

# Step 3: Transfer files
echo ""
echo "📤 Step 3: Transferring files..."
scp docker-compose.postgresql.yml $QNAP_USER@$QNAP_HOST:$DEPLOY_PATH/docker-compose.yml
scp nginx.conf $QNAP_USER@$QNAP_HOST:$DEPLOY_PATH/
scp regions_report.json $QNAP_USER@$QNAP_HOST:$DEPLOY_PATH/
scp -r scrapers/* $QNAP_USER@$QNAP_HOST:$DEPLOY_PATH/scrapers/
scp dashboard/index.html $QNAP_USER@$QNAP_HOST:$DEPLOY_PATH/dashboard/

echo "  ✅ Files transferred"

# Step 4: Deploy with Docker Compose
echo ""
echo "🐳 Step 4: Deploying with Docker Compose..."
ssh $QNAP_USER@$QNAP_HOST "
    cd $DEPLOY_PATH
    
    # Pull latest images
    echo '  📥 Pulling latest images...'
    /share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker pull postgres:15-alpine
    /share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker pull redis:7-alpine
    /share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker pull nginx:alpine
    /share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker pull ashishtandon9/openpolicyashback:latest
    
    # Deploy with docker-compose
    echo '  🚀 Starting services...'
    /share/ZFS530_DATA/.qpkg/container-station/usr/local/lib/docker/cli-plugins/docker-compose up -d
    
    echo '  ✅ Docker Compose deployment completed'
"

# Step 5: Wait for services to start
echo ""
echo "⏳ Step 5: Waiting for services to start..."
sleep 30

# Step 6: Verify deployment
echo ""
echo "🔍 Step 6: Verifying deployment..."

# Check container status
echo "  📊 Container Status:"
ssh $QNAP_USER@$QNAP_HOST '
    /share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
'

# Check service health
echo ""
echo "  🏥 Service Health:"
ssh $QNAP_USER@$QNAP_HOST '
    echo "    • PostgreSQL: $(curl -s http://localhost:5432 >/dev/null && echo "✅" || echo "❌")"
    echo "    • Redis: $(curl -s http://localhost:6379 >/dev/null && echo "✅" || echo "❌")"
    echo "    • API: $(curl -s http://localhost:8000/health >/dev/null && echo "✅" || echo "❌")"
    echo "    • Dashboard: $(curl -s http://localhost:3000 >/dev/null && echo "✅" || echo "❌")"
    echo "    • Flower: $(curl -s http://localhost:5555 >/dev/null && echo "✅" || echo "❌")"
'

# Step 7: Initialize database
echo ""
echo "🗄️ Step 7: Initializing database..."
ssh $QNAP_USER@$QNAP_HOST "
    cd $DEPLOY_PATH
    
    # Wait for PostgreSQL to be ready
    echo '  ⏳ Waiting for PostgreSQL to be ready...'
    for i in {1..30}; do
        if /share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker exec openpolicy_postgres pg_isready -U openpolicy -d opencivicdata >/dev/null 2>&1; then
            echo '  ✅ PostgreSQL is ready'
            break
        fi
        sleep 2
    done
    
    # Initialize database schema
    echo '  📝 Initializing database schema...'
    /share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker exec openpolicy_api python -c '
from src.database.models import Base
from src.database.config import engine
Base.metadata.create_all(bind=engine)
print("Database schema created successfully")
'
    
    echo '  ✅ Database initialization completed'
"

# Step 8: Final verification
echo ""
echo "🎯 Step 8: Final verification..."

# Test API endpoints
echo "  🔗 Testing API endpoints:"
ssh $QNAP_USER@$QNAP_HOST '
    echo "    • Health: $(curl -s http://localhost:8000/health | jq -r .status 2>/dev/null || echo "❌")"
    echo "    • Stats: $(curl -s http://localhost:8000/stats | jq -r .jurisdictions 2>/dev/null || echo "❌")"
    echo "    • Jurisdictions: $(curl -s http://localhost:8000/jurisdictions | jq length 2>/dev/null || echo "❌")"
'

# Display access information
echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "🌐 Access URLs:"
echo "==============="
echo "  • API: http://$QNAP_HOST:8000"
echo "  • API Docs: http://$QNAP_HOST:8000/docs"
echo "  • Dashboard: http://$QNAP_HOST:3000"
echo "  • Flower Monitor: http://$QNAP_HOST:5555"
echo ""
echo "🗄️ Database:"
echo "============"
echo "  • Host: $QNAP_HOST:5432"
echo "  • Database: opencivicdata"
echo "  • Username: openpolicy"
echo "  • Password: openpolicy123"
echo ""
echo "📊 Monitoring:"
echo "============="
echo "  • Check logs: ssh $QNAP_USER@$QNAP_HOST 'cd $DEPLOY_PATH && /share/ZFS530_DATA/.qpkg/container-station/usr/local/lib/docker/cli-plugins/docker-compose logs -f'"
echo "  • Restart services: ssh $QNAP_USER@$QNAP_HOST 'cd $DEPLOY_PATH && /share/ZFS530_DATA/.qpkg/container-station/usr/local/lib/docker/cli-plugins/docker-compose restart'"
echo "  • Stop services: ssh $QNAP_USER@$QNAP_HOST 'cd $DEPLOY_PATH && /share/ZFS530_DATA/.qpkg/container-station/usr/local/lib/docker/cli-plugins/docker-compose down'"
echo ""
echo "✅ OpenPolicy PostgreSQL system is now running!" 