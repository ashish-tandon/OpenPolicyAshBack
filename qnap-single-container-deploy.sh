#!/bin/bash

echo "🚀 Creating Single-Container OpenPolicy Deployment for QNAP"
echo "=========================================================="
echo ""

QNAP_HOST="192.168.2.152"
QNAP_USER="ashish101"
QNAP_PATH="/share/Container/openpolicy"

echo "📝 Creating single-container docker-compose.yml..."
cat > qnap-single-container.yml << 'EOF'
version: '3.8'
services:
  openpolicy_all_in_one:
    image: ashishtandon9/openpolicyashback:latest
    container_name: openpolicy_all_in_one
    environment:
      # Database settings (using SQLite for simplicity)
      DATABASE_URL: sqlite:///app/data/openpolicy.db
      # Redis settings (using in-memory for simplicity)
      REDIS_URL: redis://localhost:6379/0
      # API settings
      CORS_ORIGINS: "http://192.168.2.152:3000,http://localhost:3000,http://192.168.2.152:8080"
      # All-in-one mode
      ALL_IN_ONE_MODE: "true"
      # Ports for all services
      API_PORT: 8000
      DASHBOARD_PORT: 3000
      FLOWER_PORT: 5555
      REDIS_PORT: 6379
    ports:
      - "8000:8000"  # API
      - "3000:3000"  # Dashboard
      - "5555:5555"  # Flower Monitor
      - "6379:6379"  # Redis
    volumes:
      - /share/Container/openpolicy/data:/app/data
      - /share/Container/openpolicy/regions_report.json:/app/regions_report.json:ro
      - /share/Container/openpolicy/scrapers:/app/scrapers:ro
    restart: unless-stopped
    networks:
      - openpolicy_network
    command: >
      sh -c "
        echo '🚀 Starting OpenPolicy All-in-One Container...' &&
        echo '📊 Starting Redis server...' &&
        redis-server --daemonize yes &&
        echo '🗄️ Initializing database...' &&
        python -c 'from src.database.models import Base; from src.database.config import engine; Base.metadata.create_all(bind=engine)' &&
        echo '🌐 Starting API server...' &&
        uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
        echo '📈 Starting Celery worker...' &&
        celery -A src.scheduler.tasks worker --loglevel=info &
        echo '⏰ Starting Celery beat...' &&
        celery -A src.scheduler.tasks beat --loglevel=info &
        echo '🌸 Starting Flower monitor...' &&
        celery -A src.scheduler.tasks flower --port=5555 &
        echo '🎨 Starting Dashboard server...' &&
        python -m http.server 3000 --directory /app/dashboard &
        echo '✅ All services started!' &&
        echo '🌐 API: http://192.168.2.152:8000' &&
        echo '📊 Dashboard: http://192.168.2.152:3000' &&
        echo '📈 Flower: http://192.168.2.152:5555' &&
        tail -f /dev/null
      "

networks:
  openpolicy_network:
    driver: bridge
EOF

echo "📁 Creating data directory..."
ssh $QNAP_USER@$QNAP_HOST "mkdir -p $QNAP_PATH/data"

echo "📤 Transferring configuration..."
scp qnap-single-container.yml $QNAP_USER@$QNAP_HOST:$QNAP_PATH/docker-compose.yml

echo "📝 Creating startup script..."
cat > qnap-start-single.sh << 'EOF'
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
EOF

chmod +x qnap-start-single.sh
scp qnap-start-single.sh $QNAP_USER@$QNAP_HOST:$QNAP_PATH/

echo "📝 Creating management scripts..."
cat > qnap-stop-single.sh << 'EOF'
#!/bin/bash
echo "⏹️ Stopping OpenPolicy All-in-One..."
cd /share/Container/openpolicy
docker-compose down
echo "✅ Container stopped!"
EOF

cat > qnap-logs-single.sh << 'EOF'
#!/bin/bash
echo "📋 OpenPolicy All-in-One Logs..."
cd /share/Container/openpolicy
docker-compose logs -f
EOF

cat > qnap-status-single.sh << 'EOF'
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
EOF

chmod +x qnap-stop-single.sh qnap-logs-single.sh qnap-status-single.sh
scp qnap-stop-single.sh qnap-logs-single.sh qnap-status-single.sh $QNAP_USER@$QNAP_HOST:$QNAP_PATH/

echo "✅ Single-container deployment ready!"
echo ""
echo "📋 Next Steps:"
echo "=============="
echo "1. Open QNAP Container Station:"
echo "   http://192.168.2.152:8080"
echo ""
echo "2. Create Application:"
echo "   - Click 'Create' → 'Application'"
echo "   - Click 'Import from docker-compose.yml'"
echo "   - Upload: /share/Container/openpolicy/docker-compose.yml"
echo "   - Click 'Create'"
echo ""
echo "3. Start the Application:"
echo "   - Click 'Start'"
echo "   - Wait 2-3 minutes for startup"
echo ""
echo "4. Or run via SSH:"
echo "   ssh $QNAP_USER@$QNAP_HOST 'cd $QNAP_PATH && ./qnap-start-single.sh'"
echo ""
echo "🌐 After deployment:"
echo "==================="
echo "• API: http://192.168.2.152:8000"
echo "• Dashboard: http://192.168.2.152:3000"
echo "• Flower Monitor: http://192.168.2.152:5555"
echo ""
echo "📊 Management Commands:"
echo "======================"
echo "• Status: ./qnap-status-single.sh"
echo "• Logs: ./qnap-logs-single.sh"
echo "• Stop: ./qnap-stop-single.sh"
echo "• Start: ./qnap-start-single.sh" 