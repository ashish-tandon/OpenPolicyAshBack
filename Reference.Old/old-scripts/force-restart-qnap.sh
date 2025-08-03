#!/bin/bash

echo "🔄 Force Restarting OpenPolicy Container on QNAP"
echo "=============================================="
echo ""

QNAP_HOST="192.168.2.152"
QNAP_USER="ashish101"
CONTAINER_PATH="/share/Container/container-station-data/application/openpolicy_all_in_one"

echo "📋 Current Status:"
echo "=================="
ssh $QNAP_USER@$QNAP_HOST 'netstat -tlnp 2>/dev/null | grep -E ":(8000|3000|5555|6379)" | wc -l' | read -r PORT_COUNT
echo "  📊 Ports listening: $PORT_COUNT/4"

echo ""
echo "🚀 Force Restart Strategy:"
echo "========================="
echo "1. Backup current configuration"
echo "2. Update docker-compose.yml with restart policy"
echo "3. Force Container Station to detect changes"
echo "4. Monitor restart progress"
echo ""

echo "📁 Step 1: Backup Configuration..."
ssh $QNAP_USER@$QNAP_HOST "cp $CONTAINER_PATH/docker-compose.yml $CONTAINER_PATH/docker-compose.yml.backup.$(date +%s)"

echo "📝 Step 2: Update Configuration..."
ssh $QNAP_USER@$QNAP_HOST "sed -i 's/restart: unless-stopped/restart: always/' $CONTAINER_PATH/docker-compose.yml"

echo "🔄 Step 3: Force Container Station Detection..."
ssh $QNAP_USER@$QNAP_HOST "touch $CONTAINER_PATH/docker-compose.yml"
ssh $QNAP_USER@$QNAP_HOST "touch $CONTAINER_PATH/docker-compose.resource.yml"

echo "⏳ Step 4: Wait for restart..."
sleep 10

echo "📊 Step 5: Monitor Restart Progress..."
for i in {1..12}; do
    echo "  🔍 Check $i/12..."
    
    # Check if ports are still listening
    PORT_COUNT=$(ssh $QNAP_USER@$QNAP_HOST 'netstat -tlnp 2>/dev/null | grep -E ":(8000|3000|5555|6379)" | wc -l')
    
    if [ "$PORT_COUNT" -eq 0 ]; then
        echo "    ⏹️ Container stopped - restarting..."
    elif [ "$PORT_COUNT" -eq 4 ]; then
        echo "    ✅ All ports listening - checking services..."
        
        # Test API
        API_RESPONSE=$(ssh $QNAP_USER@$QNAP_HOST 'curl -s http://localhost:8000/health -m 5 2>/dev/null')
        if [ $? -eq 0 ] && [ ! -z "$API_RESPONSE" ]; then
            echo "    🎉 API is responding: $API_RESPONSE"
            echo ""
            echo "✅ SUCCESS: Container restarted successfully!"
            echo ""
            echo "🌐 Access URLs:"
            echo "=============="
            echo "  • API: http://$QNAP_HOST:8000"
            echo "  • Dashboard: http://$QNAP_HOST:3000"
            echo "  • Flower Monitor: http://$QNAP_HOST:5555"
            echo "  • API Docs: http://$QNAP_HOST:8000/docs"
            exit 0
        else
            echo "    ⏳ API not ready yet..."
        fi
    else
        echo "    ⚠️ Partial restart: $PORT_COUNT/4 ports listening"
    fi
    
    sleep 10
done

echo ""
echo "❌ Restart may have failed or is taking longer than expected"
echo "💡 Please check Container Station web interface:"
echo "   http://$QNAP_HOST:8080"
echo ""
echo "📋 Manual Steps:"
echo "================"
echo "1. Open Container Station"
echo "2. Find OpenPolicyAshBack application"
echo "3. Click 'Stop' then 'Start'"
echo "4. Wait 2-3 minutes for startup" 