#!/bin/bash

# OpenPolicy QNAP Complete Validation Script
# Run this from your Mac terminal

echo "================================================"
echo "🔍 OPENPOLICY COMPLETE STATUS CHECK"
echo "================================================"
echo "Time: $(date)"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

QNAP_HOST="192.168.2.152"
QNAP_USER="ashish101"

echo "1️⃣  CHECKING CONTAINER STATUS..."
echo "================================"
ssh $QNAP_USER@$QNAP_HOST 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep openpolicy' || echo "Failed to get container status"
echo ""

echo "2️⃣  CHECKING API CONTAINER SPECIFICALLY..."
echo "========================================="
ssh $QNAP_USER@$QNAP_HOST 'docker ps -a | grep -E "openpolicy.*api|openpolicy_api"' || echo "API container not found!"
echo ""

echo "3️⃣  STARTING API CONTAINER IF NEEDED..."
echo "======================================="
ssh $QNAP_USER@$QNAP_HOST 'if ! docker ps | grep -q openpolicy_api; then echo "Starting API container..."; cd /share/Container/openpolicy && docker-compose up -d api; else echo "API container already running"; fi'
echo ""

echo "4️⃣  TESTING API ENDPOINTS..."
echo "============================"
echo -n "Health Check: "
curl -s http://$QNAP_HOST:8000/health 2>/dev/null | jq '.' || echo -e "${RED}API NOT RESPONDING${NC}"
echo ""
echo -n "Stats Check: "
curl -s http://$QNAP_HOST:8000/stats 2>/dev/null | jq '.' || echo -e "${RED}Stats endpoint not available${NC}"
echo ""

echo "5️⃣  CHECKING DATABASE STATUS..."
echo "================================"
echo "Database tables:"
ssh $QNAP_USER@$QNAP_HOST 'docker exec openpolicy_postgres psql -U openpolicy -d opencivicdata -c "SELECT COUNT(*) as table_count FROM pg_tables WHERE schemaname = '\''public'\'';" 2>/dev/null' || echo "Database check failed"
echo ""

echo "Data counts:"
ssh $QNAP_USER@$QNAP_HOST 'docker exec openpolicy_postgres psql -U openpolicy -d opencivicdata -t -c "
SELECT '\''Jurisdictions: '\'' || COUNT(*) FROM ocd_jurisdiction
UNION ALL
SELECT '\''People: '\'' || COUNT(*) FROM ocd_person  
UNION ALL
SELECT '\''Organizations: '\'' || COUNT(*) FROM ocd_organization
UNION ALL
SELECT '\''Bills: '\'' || COUNT(*) FROM ocd_bill;" 2>/dev/null' || echo "No data yet or tables not created"
echo ""

echo "6️⃣  CHECKING REDIS STATUS..."
echo "============================="
ssh $QNAP_USER@$QNAP_HOST 'docker exec openpolicy_redis redis-cli ping' || echo "Redis not responding"
ssh $QNAP_USER@$QNAP_HOST 'docker exec openpolicy_redis redis-cli info keyspace | grep -E "^db|keys"' || echo "No Redis keys"
echo ""

echo "7️⃣  CHECKING WORKER STATUS..."
echo "=============================="
echo "Active workers:"
curl -s http://$QNAP_HOST:5555/api/workers 2>/dev/null | jq 'keys' || echo "Flower not accessible"
echo ""
echo "Active tasks:"
curl -s http://$QNAP_HOST:5555/api/tasks?state=ACTIVE 2>/dev/null | jq 'length' || echo "0"
echo ""

echo "8️⃣  CHECKING RECENT LOGS..."
echo "============================"
echo "=== API Logs (last 5 lines) ==="
ssh $QNAP_USER@$QNAP_HOST 'docker logs --tail 5 openpolicy_api 2>&1' || echo "No API logs"
echo ""
echo "=== Worker Logs (last 5 lines) ==="
ssh $QNAP_USER@$QNAP_HOST 'docker logs --tail 5 openpolicy_worker 2>&1' || echo "No worker logs"
echo ""

echo "9️⃣  TESTING DASHBOARD..."
echo "========================="
echo -n "Dashboard HTTP Status: "
curl -s -o /dev/null -w "%{http_code}" http://$QNAP_HOST:3000 || echo "Dashboard not accessible"
echo ""
echo ""

echo "🔟 QUICK ACCESS LINKS:"
echo "======================"
echo -e "${GREEN}Dashboard:${NC} http://$QNAP_HOST:3000"
echo -e "${GREEN}API Docs:${NC} http://$QNAP_HOST:8000/docs"
echo -e "${GREEN}Flower Monitor:${NC} http://$QNAP_HOST:5555"
echo ""

echo "📊 STARTING A TEST SCRAPE..."
echo "============================"
echo "Initiating test scrape task..."
TASK_RESPONSE=$(curl -s -X POST http://$QNAP_HOST:8000/scheduling/schedule \
  -H "Content-Type: application/json" \
  -d '{"task_type": "test"}' 2>/dev/null)
  
if [ ! -z "$TASK_RESPONSE" ]; then
    echo "Task Response: $TASK_RESPONSE"
    TASK_ID=$(echo $TASK_RESPONSE | jq -r '.task_id' 2>/dev/null)
    if [ ! -z "$TASK_ID" ] && [ "$TASK_ID" != "null" ]; then
        echo -e "${GREEN}✅ Test scrape started! Task ID: $TASK_ID${NC}"
        echo "Monitor progress at: http://$QNAP_HOST:5555"
    fi
else
    echo -e "${RED}❌ Failed to start test scrape${NC}"
fi
echo ""

echo "================================================"
echo "📈 SYSTEM STATUS SUMMARY"
echo "================================================"
echo ""

# Final status summary
if curl -s http://$QNAP_HOST:8000/health >/dev/null 2>&1; then
    echo -e "API Status: ${GREEN}✅ ONLINE${NC}"
else
    echo -e "API Status: ${RED}❌ OFFLINE${NC}"
fi

if curl -s http://$QNAP_HOST:3000 >/dev/null 2>&1; then
    echo -e "Dashboard Status: ${GREEN}✅ ONLINE${NC}"
else
    echo -e "Dashboard Status: ${RED}❌ OFFLINE${NC}"
fi

if curl -s http://$QNAP_HOST:5555 >/dev/null 2>&1; then
    echo -e "Flower Monitor: ${GREEN}✅ ONLINE${NC}"
else
    echo -e "Flower Monitor: ${RED}❌ OFFLINE${NC}"
fi

echo ""
echo "================================================"
echo "✅ Validation complete!"
echo "================================================"