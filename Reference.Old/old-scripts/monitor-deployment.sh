#!/bin/bash

echo "🔍 Monitoring OpenPolicy Deployment Status"
echo "========================================="
echo ""

QNAP_HOST="192.168.2.152"
QNAP_USER="ashish101"

echo "📊 Checking Service Status..."
echo "============================"

# Check if ports are listening
echo "🔌 Port Status:"
ssh $QNAP_USER@$QNAP_HOST 'netstat -tlnp 2>/dev/null | grep -E ":(8000|3000|5555|6379)" | while read line; do echo "  ✅ $line"; done'

echo ""
echo "🌐 Service Health Checks:"
echo "========================"

# Test API Health
echo "🔍 Testing API Health..."
API_RESPONSE=$(ssh $QNAP_USER@$QNAP_HOST 'curl -s http://localhost:8000/health -m 5 2>/dev/null')
if [ $? -eq 0 ] && [ ! -z "$API_RESPONSE" ]; then
    echo "  ✅ API Health: $API_RESPONSE"
else
    echo "  ❌ API Health: Not responding"
fi

# Test Dashboard
echo "🔍 Testing Dashboard..."
DASHBOARD_RESPONSE=$(ssh $QNAP_USER@$QNAP_HOST 'curl -s http://localhost:3000 -m 5 2>/dev/null | head -1')
if [ $? -eq 0 ] && [ ! -z "$DASHBOARD_RESPONSE" ]; then
    echo "  ✅ Dashboard: Responding"
else
    echo "  ❌ Dashboard: Not responding"
fi

# Test Flower Monitor
echo "🔍 Testing Flower Monitor..."
FLOWER_RESPONSE=$(ssh $QNAP_USER@$QNAP_HOST 'curl -s http://localhost:5555 -m 5 2>/dev/null | head -1')
if [ $? -eq 0 ] && [ ! -z "$FLOWER_RESPONSE" ]; then
    echo "  ✅ Flower Monitor: Responding"
else
    echo "  ❌ Flower Monitor: Not responding"
fi

echo ""
echo "📈 System Summary:"
echo "=================="

# Count working services
WORKING_SERVICES=0
if [ $? -eq 0 ] && [ ! -z "$API_RESPONSE" ]; then
    WORKING_SERVICES=$((WORKING_SERVICES + 1))
fi
if [ $? -eq 0 ] && [ ! -z "$DASHBOARD_RESPONSE" ]; then
    WORKING_SERVICES=$((WORKING_SERVICES + 1))
fi
if [ $? -eq 0 ] && [ ! -z "$FLOWER_RESPONSE" ]; then
    WORKING_SERVICES=$((WORKING_SERVICES + 1))
fi

echo "  📊 Services Working: $WORKING_SERVICES/3"

if [ $WORKING_SERVICES -eq 3 ]; then
    echo "  🎉 Status: FULLY OPERATIONAL"
    echo ""
    echo "🌐 Access URLs:"
    echo "=============="
    echo "  • API: http://$QNAP_HOST:8000"
    echo "  • Dashboard: http://$QNAP_HOST:3000"
    echo "  • Flower Monitor: http://$QNAP_HOST:5555"
    echo "  • API Docs: http://$QNAP_HOST:8000/docs"
elif [ $WORKING_SERVICES -eq 2 ]; then
    echo "  ⚠️  Status: PARTIALLY WORKING"
    echo "  💡 API may need restart with fixed image"
elif [ $WORKING_SERVICES -eq 1 ]; then
    echo "  ❌ Status: MOSTLY FAILED"
    echo "  🔧 Container needs restart"
else
    echo "  💥 Status: COMPLETELY FAILED"
    echo "  🚨 Container needs immediate attention"
fi

echo ""
echo "📋 Next Steps:"
echo "=============="
if [ $WORKING_SERVICES -lt 3 ]; then
    echo "1. Restart container in Container Station"
    echo "2. Wait 2-3 minutes for startup"
    echo "3. Run this script again to verify"
else
    echo "✅ System is fully operational!"
    echo "🎯 Data scraping will begin automatically"
    echo "📊 Monitor progress at http://$QNAP_HOST:5555"
fi 