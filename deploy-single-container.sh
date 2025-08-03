#!/bin/bash

# OpenPolicy Single Container Deployment Script
# This script deploys everything in ONE container

set -e

echo "🚀 OpenPolicy Single Container Deployment"
echo "========================================"
echo ""

# Configuration
QNAP_HOST="192.168.2.152"
QNAP_USER="ashish101"
DEPLOY_PATH="/share/Container/openpolicy-single"

echo "📋 Configuration:"
echo "=================="
echo "  • QNAP Host: $QNAP_HOST"
echo "  • QNAP User: $QNAP_USER"
echo "  • Deploy Path: $DEPLOY_PATH"
echo "  • Architecture: Single Container (PostgreSQL + Redis + API + Dashboard)"
echo ""

# Step 1: Stop and remove existing containers
echo "🛑 Step 1: Cleaning up existing containers..."
ssh $QNAP_USER@$QNAP_HOST '
    # Stop and remove existing containers
    /share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker stop openpolicy_all_in_one 2>/dev/null || true
    /share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker rm openpolicy_all_in_one 2>/dev/null || true
    /share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker stop openpolicy_single 2>/dev/null || true
    /share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker rm openpolicy_single 2>/dev/null || true
    
    # Remove old images
    /share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker rmi ashishtandon9/openpolicyashback:all-in-one 2>/dev/null || true
    /share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker rmi openpolicy-single:latest 2>/dev/null || true
    
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
scp Dockerfile.single-container $QNAP_USER@$QNAP_HOST:$DEPLOY_PATH/Dockerfile
scp docker-compose.single.yml $QNAP_USER@$QNAP_HOST:$DEPLOY_PATH/docker-compose.yml
scp supervisord.conf $QNAP_USER@$QNAP_HOST:$DEPLOY_PATH/
scp nginx.conf $QNAP_USER@$QNAP_HOST:$DEPLOY_PATH/
scp requirements.txt $QNAP_USER@$QNAP_HOST:$DEPLOY_PATH/
scp regions_report.json $QNAP_USER@$QNAP_HOST:$DEPLOY_PATH/
scp -r src/ $QNAP_USER@$QNAP_HOST:$DEPLOY_PATH/
scp -r scrapers/ $QNAP_USER@$QNAP_HOST:$DEPLOY_PATH/
scp -r dashboard/ $QNAP_USER@$QNAP_HOST:$DEPLOY_PATH/

echo "  ✅ Files transferred"

# Step 4: Build and deploy
echo ""
echo "🐳 Step 4: Building and deploying single container..."
ssh $QNAP_USER@$QNAP_HOST "
    cd $DEPLOY_PATH
    
    # Build the single container image
    echo '  🔨 Building single container image...'
    /share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker build -t openpolicy-single:latest .
    
    # Deploy with docker-compose
    echo '  🚀 Starting single container...'
    /share/ZFS530_DATA/.qpkg/container-station/usr/local/lib/docker/cli-plugins/docker-compose up -d
    
    echo '  ✅ Single container deployment completed'
"

# Step 5: Wait for services to start
echo ""
echo "⏳ Step 5: Waiting for services to start..."
sleep 60

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
    echo "    • API: $(curl -s http://localhost:8000/health >/dev/null && echo "✅" || echo "❌")"
    echo "    • Dashboard: $(curl -s http://localhost:3000 >/dev/null && echo "✅" || echo "❌")"
    echo "    • Flower: $(curl -s http://localhost:5555 >/dev/null && echo "✅" || echo "❌")"
    echo "    • PostgreSQL: $(/share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker exec openpolicy_single pg_isready -U openpolicy -d opencivicdata >/dev/null 2>&1 && echo "✅" || echo "❌")"
    echo "    • Redis: $(/share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker exec openpolicy_single redis-cli ping >/dev/null 2>&1 && echo "✅" || echo "❌")"
'

# Step 7: Test API endpoints
echo ""
echo "🎯 Step 7: Testing API endpoints..."
ssh $QNAP_USER@$QNAP_HOST '
    echo "    • Health: $(curl -s http://localhost:8000/health | jq -r .status 2>/dev/null || echo "❌")"
    echo "    • Stats: $(curl -s http://localhost:8000/stats | jq -r .jurisdictions 2>/dev/null || echo "❌")"
    echo "    • Jurisdictions: $(curl -s http://localhost:8000/jurisdictions | jq length 2>/dev/null || echo "❌")"
'

# Display access information
echo ""
echo "🎉 Single Container Deployment Complete!"
echo "======================================="
echo ""
echo "🌐 Access URLs:"
echo "==============="
echo "  • API: http://$QNAP_HOST:8000"
echo "  • API Docs: http://$QNAP_HOST:8000/docs"
echo "  • Dashboard: http://$QNAP_HOST:3000"
echo "  • Flower Monitor: http://$QNAP_HOST:5555"
echo ""
echo "🗄️ Database (Internal):"
echo "======================"
echo "  • Host: localhost:5432 (inside container)"
echo "  • Database: opencivicdata"
echo "  • Username: openpolicy"
echo "  • Password: openpolicy123"
echo ""
echo "📊 Monitoring:"
echo "============="
echo "  • Check logs: ssh $QNAP_USER@$QNAP_HOST '/share/ZFS530_DATA/.qpkg/container-station/usr/bin/.libs/docker logs -f openpolicy_single'"
echo "  • Restart container: ssh $QNAP_USER@$QNAP_HOST 'cd $DEPLOY_PATH && /share/ZFS530_DATA/.qpkg/container-station/usr/local/lib/docker/cli-plugins/docker-compose restart'"
echo "  • Stop container: ssh $QNAP_USER@$QNAP_HOST 'cd $DEPLOY_PATH && /share/ZFS530_DATA/.qpkg/container-station/usr/local/lib/docker/cli-plugins/docker-compose down'"
echo ""
echo "✅ OpenPolicy Single Container system is now running!"
echo "🎯 Everything is in ONE container: PostgreSQL + Redis + API + Dashboard + Celery!" 