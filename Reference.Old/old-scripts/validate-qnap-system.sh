#!/bin/bash

echo "🔍 OpenPolicy QNAP System Validation Report"
echo "=========================================="
echo "Timestamp: $(date)"
echo ""

# Check if we can access the QNAP server
QNAP_HOST="192.168.2.152"
QNAP_USER="ashish101"

echo "📡 Testing QNAP Connectivity..."
if ssh -o ConnectTimeout=5 $QNAP_USER@$QNAP_HOST "echo 'Connected'" 2>/dev/null; then
    echo "✅ SSH connection to QNAP successful"
else
    echo "❌ SSH connection to QNAP failed"
    exit 1
fi

echo ""
echo "🐳 Container Status Check..."
echo "=========================="

# Check container status via SSH
ssh $QNAP_USER@$QNAP_HOST << 'EOF'
echo "Checking running containers..."
echo ""

# Test Dashboard (Port 3000)
echo "📊 Testing Dashboard (Port 3000)..."
if curl -s -m 5 http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Dashboard is responding"
    DASHBOARD_STATUS="✅ Working"
else
    echo "❌ Dashboard not responding"
    DASHBOARD_STATUS="❌ Not Working"
fi

# Test Flower Monitor (Port 5555)
echo "📈 Testing Flower Monitor (Port 5555)..."
if curl -s -m 5 http://localhost:5555 > /dev/null 2>&1; then
    echo "✅ Flower Monitor is responding"
    FLOWER_STATUS="✅ Working"
else
    echo "❌ Flower Monitor not responding"
    FLOWER_STATUS="❌ Not Working"
fi

# Test Redis (Port 6379)
echo "⚡ Testing Redis (Port 6379)..."
if nc -z localhost 6379 2>/dev/null; then
    echo "✅ Redis is listening"
    REDIS_STATUS="✅ Working"
else
    echo "❌ Redis not listening"
    REDIS_STATUS="❌ Not Working"
fi

# Test PostgreSQL (Port 5432)
echo "🗄️ Testing PostgreSQL (Port 5432)..."
if nc -z localhost 5432 2>/dev/null; then
    echo "✅ PostgreSQL is listening"
    POSTGRES_STATUS="✅ Working"
else
    echo "❌ PostgreSQL not listening"
    POSTGRES_STATUS="❌ Not Working"
fi

# Test API (Port 8000)
echo "🔌 Testing API (Port 8000)..."
if curl -s -m 5 http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is responding"
    API_STATUS="✅ Working"
else
    echo "❌ API not responding"
    API_STATUS="❌ Not Working"
fi

echo ""
echo "📋 Service Status Summary:"
echo "=========================="
echo "Dashboard: $DASHBOARD_STATUS"
echo "Flower Monitor: $FLOWER_STATUS"
echo "Redis: $REDIS_STATUS"
echo "PostgreSQL: $POSTGRES_STATUS"
echo "API: $API_STATUS"

echo ""
echo "🌐 Access URLs:"
echo "=============="
echo "Dashboard: http://192.168.2.152:3000"
echo "API: http://192.168.2.152:8000"
echo "Flower Monitor: http://192.168.2.152:5555"
echo "Database: localhost:5432 (from QNAP)"

echo ""
echo "🔍 Network Port Status:"
echo "======================"
netstat -tlnp 2>/dev/null | grep -E ':(8000|3000|5555|5432|6379)' || echo "netstat not available"

echo ""
echo "📊 Process Count:"
echo "================"
echo "PostgreSQL processes: $(ps aux | grep postgres | grep -v grep | wc -l)"
echo "Redis processes: $(ps aux | grep redis | grep -v grep | wc -l)"
echo "Nginx processes: $(ps aux | grep nginx | grep -v grep | wc -l)"
echo "Celery processes: $(ps aux | grep celery | grep -v grep | wc -l)"

EOF

echo ""
echo "🎯 Next Steps:"
echo "=============="
echo "1. If API is not working, check Container Station for openpolicy_api container"
echo "2. If database is not working, check PostgreSQL container logs"
echo "3. If dashboard is working, you can access it at: http://192.168.2.152:3000"
echo "4. If Flower is working, monitor tasks at: http://192.168.2.152:5555"
echo ""
echo "📈 Expected Data Scraping Timeline:"
echo "=================================="
echo "• Initial setup: 5-10 minutes"
echo "• Database initialization: 2-3 minutes"
echo "• First scraping run: 15-30 minutes"
echo "• Full data collection: 2-4 hours"
echo "• Real-time updates: Continuous"
echo ""
echo "✅ Validation complete!" 