#!/bin/bash
echo "🚀 Starting OpenPolicy All-in-One Container..."
cd /share/Container/openpolicy

echo "📥 Pulling latest image..."
docker pull ashishtandon9/openpolicyashback:latest

echo "🔄 Starting container..."
docker-compose up -d

echo "⏳ Waiting for container to start..."
sleep 30

echo "📊 Container Status:"
docker-compose ps

echo ""
echo "✅ OpenPolicy All-in-One is running!"
echo "🌐 API: http://192.168.2.152:8000"
echo "📊 Dashboard: http://192.168.2.152:3000"
echo "📈 Flower Monitor: http://192.168.2.152:5555"
echo "🗄️ Redis: localhost:6379"
