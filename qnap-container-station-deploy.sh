#!/bin/bash
set -e

echo "🚀 Starting QNAP Container Station deployment..."

# Check if Container Station is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker/Container Station is not available"
    echo "Please ensure Container Station is installed and running from QNAP App Center"
    exit 1
fi

echo "✅ Container Station is available"
docker --version

# Stop and remove existing container
echo "📦 Stopping existing container..."
docker stop openpolicy_single 2>/dev/null || true
docker rm openpolicy_single 2>/dev/null || true

# Remove old image
echo "🗑️ Removing old image..."
docker rmi ashishtandon/openpolicy-single:latest 2>/dev/null || true

# Pull latest image
echo "⬇️ Pulling latest image from Docker Hub..."
if docker pull ashishtandon/openpolicy-single:latest; then
    echo "✅ Image pulled successfully"
else
    echo "❌ Failed to pull image"
    echo "Trying to build image locally..."
    
    # Create a simple Dockerfile for local build
    cat > Dockerfile.local << 'DOCKER_EOF'
FROM debian:bullseye-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    postgresql \
    redis-server \
    curl \
    nginx \
    supervisor \
    nodejs \
    npm \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Build dashboard
WORKDIR /app/dashboard
RUN npm ci --only=production && npm run build
WORKDIR /app

# Create necessary directories
RUN mkdir -p /var/log/nginx /var/log/supervisor

# Copy configuration files
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY nginx.conf /etc/nginx/nginx.conf

# Create start script
RUN echo '#!/bin/bash\nset -e\n\n# Start services\n/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf\n\n# Keep container running\nexec "$@"' > /app/start.sh && chmod +x /app/start.sh

# Expose ports
EXPOSE 80 8000 3000 5555 6379 5432

# Start command
CMD ["/app/start.sh"]
DOCKER_EOF

    # Build image locally
    if docker build -f Dockerfile.local -t ashishtandon/openpolicy-single:latest .; then
        echo "✅ Image built successfully"
        rm Dockerfile.local
    else
        echo "❌ Failed to build image locally"
        exit 1
    fi
fi

# Create docker-compose file for Container Station
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
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  postgres_data:
    driver: local
COMPOSE_EOF

# Start the container using docker-compose
echo "🚀 Starting the container..."
if docker-compose up -d; then
    echo "✅ Container started successfully"
else
    echo "❌ Failed to start container with docker-compose"
    echo "Trying direct docker run..."
    
    # Fallback to direct docker run
    docker run -d \
        --name openpolicy_single \
        --restart unless-stopped \
        -p 80:80 \
        -p 8000:8000 \
        -p 3000:3000 \
        -p 5555:5555 \
        -p 6379:6379 \
        -p 5432:5432 \
        -e DATABASE_URL=postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata \
        -e REDIS_URL=redis://localhost:6379/0 \
        -e CORS_ORIGINS=http://localhost:3000,http://localhost:80,http://192.168.2.152,http://ashishsnas.myqnapcloud.com \
        -e NODE_ENV=production \
        -v postgres_data:/var/lib/postgresql/data \
        ashishtandon/openpolicy-single:latest
    
    if [ $? -eq 0 ]; then
        echo "✅ Container started successfully with docker run"
    else
        echo "❌ Failed to start container"
        exit 1
    fi
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

echo "✅ QNAP Container Station deployment completed successfully"
