#!/bin/bash

# QNAP Container Station Deployment for OpenPolicy
echo "🚀 Deploying OpenPolicy using QNAP Container Station..."

QNAP_HOST="192.168.2.152"
QNAP_USER="ashish101"
QNAP_PATH="/share/Container/openpolicy"

# Create a QNAP-specific docker-compose file
echo "📝 Creating QNAP Container Station configuration..."

cat > qnap-docker-compose.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:17
    container_name: openpolicy_postgres
    environment:
      POSTGRES_DB: opencivicdata
      POSTGRES_USER: openpolicy
      POSTGRES_PASSWORD: openpolicy123
      POSTGRES_HOST_AUTH_METHOD: trust
    volumes:
      - /share/Container/openpolicy/postgres_data:/var/lib/postgresql/data
      - /share/Container/openpolicy/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - openpolicy_network

  # Redis for Celery
  redis:
    image: redis:7-alpine
    container_name: openpolicy_redis
    ports:
      - "6379:6379"
    volumes:
      - /share/Container/openpolicy/redis_data:/data
    restart: unless-stopped
    networks:
      - openpolicy_network

  # OpenPolicy Database API
  api:
    image: ashishtandon9/openpolicyashback:latest
    container_name: openpolicy_api
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: opencivicdata
      DB_USER: openpolicy
      DB_PASSWORD: openpolicy123
      REDIS_URL: redis://redis:6379/0
      CORS_ORIGINS: "http://192.168.2.152:3000,http://localhost:3000,https://dashboard-h1ilgrlf8-ashish-tandons-projects.vercel.app"
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    volumes:
      - /share/Container/openpolicy/regions_report.json:/app/regions_report.json:ro
      - /share/Container/openpolicy/scrapers:/app/scrapers:ro
    restart: unless-stopped
    networks:
      - openpolicy_network

  # Celery Worker
  celery_worker:
    image: ashishtandon9/openpolicyashback:latest
    container_name: openpolicy_worker
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: opencivicdata
      DB_USER: openpolicy
      DB_PASSWORD: openpolicy123
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - /share/Container/openpolicy/regions_report.json:/app/regions_report.json:ro
      - /share/Container/openpolicy/scrapers:/app/scrapers:ro
    restart: unless-stopped
    command: ["celery", "-A", "src.scheduler.tasks", "worker", "--loglevel=info"]
    networks:
      - openpolicy_network

  # Celery Beat (Scheduler)
  celery_beat:
    image: ashishtandon9/openpolicyashback:latest
    container_name: openpolicy_beat
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: opencivicdata
      DB_USER: openpolicy
      DB_PASSWORD: openpolicy123
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - /share/Container/openpolicy/regions_report.json:/app/regions_report.json:ro
      - /share/Container/openpolicy/scrapers:/app/scrapers:ro
    restart: unless-stopped
    command: ["celery", "-A", "src.scheduler.tasks", "beat", "--loglevel=info"]
    networks:
      - openpolicy_network

  # Celery Flower (Monitoring)
  flower:
    image: mher/flower:2.0
    container_name: openpolicy_flower
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - FLOWER_PORT=5555
    depends_on:
      - redis
    restart: unless-stopped
    networks:
      - openpolicy_network

networks:
  openpolicy_network:
    driver: bridge
EOF

# Create directories for persistent data
echo "📁 Creating data directories..."
ssh $QNAP_USER@$QNAP_HOST "mkdir -p $QNAP_PATH/postgres_data $QNAP_PATH/redis_data"

# Transfer the QNAP-specific docker-compose file
echo "📤 Transferring QNAP configuration..."
scp qnap-docker-compose.yml $QNAP_USER@$QNAP_HOST:$QNAP_PATH/docker-compose.yml

# Create a QNAP startup script
cat > qnap-start.sh << 'EOF'
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
EOF

chmod +x qnap-start.sh
scp qnap-start.sh $QNAP_USER@$QNAP_HOST:$QNAP_PATH/

echo "✅ QNAP Container Station deployment ready!"
echo ""
echo "📋 Next steps:"
echo "1. Open QNAP Container Station in your web browser"
echo "2. Navigate to: http://192.168.2.152:8080"
echo "3. Or run: ssh ashish101@192.168.2.152 'cd /share/Container/openpolicy && ./qnap-start.sh'"
echo ""
echo "🌐 After deployment, your API will be at:"
echo "   http://192.168.2.152:8000" 