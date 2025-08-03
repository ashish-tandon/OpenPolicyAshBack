#!/bin/bash

echo "🔍 OPENPOLICY QNAP STATUS CHECK - $(date)"
echo "========================================"
echo ""

# Quick status checks you can run RIGHT NOW from your Mac

echo "1️⃣ CHECKING API CONTAINER STATUS:"
echo "Run this command:"
echo 'ssh ashish101@192.168.2.152 "docker ps -a | grep -E \"api|API\""'
echo ""

echo "2️⃣ CHECKING IF API IS RESPONDING:"
echo "Run this command:"
echo 'curl -s http://192.168.2.152:8000/health || echo "API NOT RESPONDING"'
echo ""

echo "3️⃣ CHECKING DATABASE TABLES:"
echo "Run this command:"
echo 'ssh ashish101@192.168.2.152 "docker exec openpolicy_postgres psql -U openpolicy -d opencivicdata -c \"SELECT COUNT(*) as table_count FROM pg_tables WHERE schemaname = '\''public'\'';\""'
echo ""

echo "4️⃣ CHECKING IF DATA IS LOADING:"
echo "Run these commands:"
echo '# Check jurisdiction count:'
echo 'ssh ashish101@192.168.2.152 "docker exec openpolicy_postgres psql -U openpolicy -d opencivicdata -c \"SELECT COUNT(*) as jurisdictions FROM ocd_jurisdiction;\""'
echo ""
echo '# Check representative count:'
echo 'ssh ashish101@192.168.2.152 "docker exec openpolicy_postgres psql -U openpolicy -d opencivicdata -c \"SELECT COUNT(*) as representatives FROM ocd_person;\""'
echo ""

echo "5️⃣ CHECKING WORKER ACTIVITY:"
echo "Run this command:"
echo 'curl -s http://192.168.2.152:5555/api/tasks?state=ACTIVE | jq "." || echo "No Flower access"'
echo ""

echo "6️⃣ QUICK DASHBOARD TEST:"
echo "Open in browser NOW:"
echo "http://192.168.2.152:3000"
echo ""

echo "7️⃣ CHECK ALL CONTAINER LOGS AT ONCE:"
echo 'ssh ashish101@192.168.2.152 "for container in openpolicy_api openpolicy_worker openpolicy_postgres; do echo \"=== \$container ===\"; docker logs --tail 10 \$container 2>&1; echo; done"'
echo ""

echo "🚨 IF API CONTAINER IS MISSING, RUN THIS:"
echo 'ssh ashish101@192.168.2.152 "cd /share/Container/openpolicy && docker-compose up -d api"'