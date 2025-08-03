#!/bin/bash
echo "📊 OpenPolicy All-in-One Status..."
cd /share/Container/openpolicy
docker-compose ps
echo ""
echo "🌐 Testing endpoints..."
echo "API Health:"
curl -s http://localhost:8000/health || echo "API not responding"
echo ""
echo "Dashboard:"
curl -s http://localhost:3000 | head -3 || echo "Dashboard not responding"
echo ""
echo "Flower:"
curl -s http://localhost:5555 | head -3 || echo "Flower not responding"
