#!/bin/bash

echo "🔍 OpenPolicy QNAP Deployment Validation Script"
echo "=============================================="
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Container IPs from Container Station
POSTGRES_IP="172.29.0.3"
REDIS_IP="172.29.0.2"
API_IP="172.29.0.6"  # Assuming API is not shown but should be around this range
WORKER_IP="172.29.0.5"
BEAT_IP="172.29.0.7"
FLOWER_IP="172.29.0.4"
DASHBOARD_IP="172.29.0.8"

echo "📊 Container Network Information:"
echo "================================="
echo "PostgreSQL: $POSTGRES_IP"
echo "Redis: $REDIS_IP"
echo "API: ~172.29.0.6"
echo "Worker: $WORKER_IP"
echo "Beat: $BEAT_IP"
echo "Flower: $FLOWER_IP"
echo "Dashboard: $DASHBOARD_IP"
echo ""

# Test from host machine
echo "🌐 Testing External Access (from your Mac):"
echo "==========================================="

echo -e "\n1️⃣ Testing API Health:"
echo "curl -s http://192.168.2.152:8000/health"
curl -s http://192.168.2.152:8000/health | jq '.' 2>/dev/null || echo "API not accessible externally"

echo -e "\n2️⃣ Testing API Stats:"
echo "curl -s http://192.168.2.152:8000/stats"
curl -s http://192.168.2.152:8000/stats | jq '.' 2>/dev/null || echo "Stats endpoint not accessible"

echo -e "\n3️⃣ Testing Dashboard:"
echo "curl -I http://192.168.2.152:3000"
curl -I http://192.168.2.152:3000 2>/dev/null | head -n 1

echo -e "\n4️⃣ Testing Flower Monitor:"
echo "curl -I http://192.168.2.152:5555"
curl -I http://192.168.2.152:5555 2>/dev/null | head -n 1

echo -e "\n5️⃣ Testing Database Connection:"
echo "PGPASSWORD=openpolicy123 psql -h 192.168.2.152 -p 5432 -U openpolicy -d opencivicdata -c '\dt'"

echo -e "\n📋 Commands to run on QNAP via SSH:"
echo "===================================="
echo ""
echo "# Check database tables:"
echo 'ssh ashish101@192.168.2.152 "docker exec openpolicy_postgres psql -U openpolicy -d opencivicdata -c \"\dt\""'
echo ""
echo "# Check database content:"
echo 'ssh ashish101@192.168.2.152 "docker exec openpolicy_postgres psql -U openpolicy -d opencivicdata -c \"SELECT COUNT(*) FROM ocd_jurisdiction;\""'
echo ""
echo "# Check Redis status:"
echo 'ssh ashish101@192.168.2.152 "docker exec openpolicy_redis redis-cli ping"'
echo ""
echo "# Check Celery worker status:"
echo 'ssh ashish101@192.168.2.152 "docker exec openpolicy_worker celery -A src.scheduler.tasks inspect active"'
echo ""
echo "# Check container logs:"
echo 'ssh ashish101@192.168.2.152 "docker logs --tail 20 openpolicy_api"'
echo ""
echo "# Check all container statuses:"
echo 'ssh ashish101@192.168.2.152 "docker ps --format \"table {{.Names}}\t{{.Status}}\t{{.Ports}}\""'

echo -e "\n📊 Data Scraping Estimates:"
echo "==========================="
echo ""
echo "Based on typical scraping rates:"
echo "- Federal data (Parliament): ~2-4 hours"
echo "- Provincial data (10 provinces): ~8-12 hours per province"
echo "- Municipal data (Major cities): ~4-6 hours per city"
echo ""
echo "Total initial data load: ~24-48 hours for comprehensive coverage"
echo "Incremental updates: ~2-4 hours daily"
echo ""
echo "Note: Actual times depend on:"
echo "- Network speed"
echo "- Source website response times"
echo "- Rate limiting policies"
echo "- Number of records to process"

echo -e "\n✅ Quick Validation URLs:"
echo "========================"
echo "1. API Health: http://192.168.2.152:8000/health"
echo "2. API Docs: http://192.168.2.152:8000/docs"
echo "3. Dashboard: http://192.168.2.152:3000"
echo "4. Flower: http://192.168.2.152:5555"
echo "5. Database: psql -h 192.168.2.152 -p 5432 -U openpolicy -d opencivicdata"