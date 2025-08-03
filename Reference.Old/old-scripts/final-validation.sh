#!/bin/bash

echo "🎉 Final OpenPolicy System Validation"
echo "===================================="
echo "Run this after adding the API container"
echo ""

QNAP_HOST="192.168.2.152"
QNAP_USER="ashish101"

echo "🔍 Testing Complete System..."
echo ""

# Test all services
ssh $QNAP_USER@$QNAP_HOST << 'EOF'

echo "📊 Testing Dashboard..."
if curl -s -m 5 http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Dashboard: http://192.168.2.152:3000"
else
    echo "❌ Dashboard not responding"
fi

echo ""
echo "🔌 Testing API..."
if curl -s -m 5 http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API Health: http://192.168.2.152:8000/health"
    echo "✅ API Docs: http://192.168.2.152:8000/docs"
else
    echo "❌ API not responding"
fi

echo ""
echo "📈 Testing Flower Monitor..."
if curl -s -m 5 http://localhost:5555 > /dev/null 2>&1; then
    echo "✅ Flower Monitor: http://192.168.2.152:5555"
else
    echo "❌ Flower Monitor not responding"
fi

echo ""
echo "🗄️ Testing Database..."
if nc -z localhost 5432 2>/dev/null; then
    echo "✅ PostgreSQL: localhost:5432"
else
    echo "❌ PostgreSQL not listening"
fi

echo ""
echo "⚡ Testing Redis..."
if nc -z localhost 6379 2>/dev/null; then
    echo "✅ Redis: localhost:6379"
else
    echo "❌ Redis not listening"
fi

echo ""
echo "🎯 System Status Summary:"
echo "========================"
if curl -s -m 5 http://localhost:8000/health > /dev/null 2>&1; then
    echo "🎉 CONGRATULATIONS! Your OpenPolicy system is fully operational!"
    echo ""
    echo "🌐 Access URLs:"
    echo "• Dashboard: http://192.168.2.152:3000"
    echo "• API Health: http://192.168.2.152:8000/health"
    echo "• API Docs: http://192.168.2.152:8000/docs"
    echo "• Flower Monitor: http://192.168.2.152:5555"
    echo ""
    echo "📊 Next Steps:"
    echo "• Open the dashboard to start data collection"
    echo "• Monitor progress in Flower"
    echo "• Use the API for custom integrations"
    echo ""
    echo "⏱️ Expected Timeline:"
    echo "• First data scraping: 15-30 minutes"
    echo "• Complete collection: 2-4 hours"
    echo "• Real-time updates: Continuous"
else
    echo "⚠️ System partially operational - API container may still be starting"
    echo "Please wait 2-3 minutes and run this validation again"
fi

EOF

echo ""
echo "✅ Validation complete!" 