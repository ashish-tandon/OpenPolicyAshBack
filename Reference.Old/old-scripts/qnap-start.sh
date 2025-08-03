#!/bin/bash

echo "🚀 Starting OpenPolicy on QNAP Container Station..."

# Navigate to the deployment directory
cd /share/Container/openpolicy

# Pull the latest images
echo "📥 Pulling Docker images..."
docker pull ashishtandon9/openpolicyashback:latest
docker pull postgres:17
docker pull redis:7-alpine
docker pull mher/flower:2.0

# Start the services
echo "🔄 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service status
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✅ OpenPolicy system is running!"
echo "🌐 API: http://192.168.2.152:8000"
echo "📊 Flower Monitor: http://192.168.2.152:5555"
echo "🗄️ Database: localhost:5432"
