#!/bin/bash
set -e

echo "🚀 Starting QNAP deployment..."

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed on QNAP"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed on QNAP"
    exit 1
fi

# Stop and remove existing container
echo "📦 Stopping existing container..."
docker stop openpolicy_single 2>/dev/null || true
docker rm openpolicy_single 2>/dev/null || true

# Remove old image
echo "🗑️ Removing old image..."
docker rmi ashishtandon/openpolicy-single:latest 2>/dev/null || true

# Pull latest image
echo "⬇️ Pulling latest image..."
if docker pull ashishtandon/openpolicy-single:latest; then
    echo "✅ Image pulled successfully"
else
    echo "❌ Failed to pull image"
    exit 1
fi

# Create docker-compose file
echo "📝 Creating docker-compose configuration..."
cat > docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  openpolicy:
    image: ashishtandon/openpolicy-single:latest
    container_name: openpolicy_single
    ports:
      - "80:80"
      - "8000:8000"
      - "3000:3000"
      - "5555:5555"
      - "6379:6379"
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - DATABASE_URL=postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata
      - REDIS_URL=redis://localhost:6379/0
      - CORS_ORIGINS=http://localhost:3000,http://localhost:80,http://192.168.2.152,http://ashishsnas.myqnapcloud.com
      - NODE_ENV=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "/app/healthcheck.sh"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  postgres_data:
    driver: local
COMPOSE_EOF

# Start the container
echo "🚀 Starting the container..."
if docker-compose up -d; then
    echo "✅ Container started successfully"
else
    echo "❌ Failed to start container"
    exit 1
fi

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Test health endpoint
echo "🏥 Testing health endpoint..."
for i in {1..10}; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ API health check passed"
        break
    else
        echo "   Attempt $i/10 - API not ready yet..."
        if [ $i -eq 10 ]; then
            echo "❌ API health check failed after 10 attempts"
            docker logs openpolicy_single
            exit 1
        fi
        sleep 10
    fi
done

# Test dashboard
echo "🖥️ Testing dashboard..."
for i in {1..5}; do
    if curl -f http://localhost:3000 >/dev/null 2>&1; then
        echo "✅ Dashboard health check passed"
        break
    else
        echo "   Attempt $i/5 - Dashboard not ready yet..."
        if [ $i -eq 5 ]; then
            echo "❌ Dashboard health check failed after 5 attempts"
            docker logs openpolicy_single
            exit 1
        fi
        sleep 10
    fi
done

# Show container status
echo "📊 Container status:"
docker ps | grep openpolicy_single

echo "✅ QNAP deployment completed successfully"
