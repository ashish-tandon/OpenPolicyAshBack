#!/bin/bash
set -e

echo "🚀 Starting simple QNAP deployment..."

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not available"
    exit 1
fi

echo "✅ Docker is available"

# Stop and remove existing containers
echo "📦 Stopping existing containers..."
docker stop openpolicy_api openpolicy_dashboard openpolicy_db openpolicy_redis 2>/dev/null || true
docker rm openpolicy_api openpolicy_dashboard openpolicy_db openpolicy_redis 2>/dev/null || true

# Create network
echo "🌐 Creating network..."
docker network create openpolicy_network 2>/dev/null || true

# Start PostgreSQL
echo "🗄️ Starting PostgreSQL..."
docker run -d \
    --name openpolicy_db \
    --network openpolicy_network \
    -e POSTGRES_DB=opencivicdata \
    -e POSTGRES_USER=openpolicy \
    -e POSTGRES_PASSWORD=openpolicy123 \
    -p 5432:5432 \
    --restart unless-stopped \
    postgres:15

# Start Redis
echo "🔴 Starting Redis..."
docker run -d \
    --name openpolicy_redis \
    --network openpolicy_network \
    -p 6379:6379 \
    --restart unless-stopped \
    redis:7-alpine

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Start FastAPI backend (using Python base image)
echo "🐍 Starting FastAPI backend..."
docker run -d \
    --name openpolicy_api \
    --network openpolicy_network \
    -p 8000:8000 \
    -e DATABASE_URL=postgresql://openpolicy:openpolicy123@openpolicy_db:5432/opencivicdata \
    -e REDIS_URL=redis://openpolicy_redis:6379/0 \
    -e CORS_ORIGINS=http://localhost:3000,http://192.168.2.152:3000,http://ashishsnas.myqnapcloud.com \
    --restart unless-stopped \
    python:3.11-slim

# Install dependencies and start API
docker exec openpolicy_api bash -c "
    apt-get update && apt-get install -y curl
    pip install fastapi uvicorn psycopg2-binary redis sqlalchemy
    echo 'from fastapi import FastAPI; app = FastAPI(); @app.get(\"/health\"); def health(): return {\"status\": \"healthy\"}; @app.get(\"/\"); def root(): return {\"message\": \"OpenPolicy API\"}' > /app/main.py
    cd /app && uvicorn main:app --host 0.0.0.0 --port 8000
" &

# Start simple web dashboard (using nginx)
echo "🌐 Starting web dashboard..."
docker run -d \
    --name openpolicy_dashboard \
    --network openpolicy_network \
    -p 3000:80 \
    -e API_URL=http://openpolicy_api:8000 \
    --restart unless-stopped \
    nginx:alpine

# Create simple dashboard
docker exec openpolicy_dashboard sh -c "
    echo '<!DOCTYPE html>
    <html>
    <head>
        <title>OpenPolicy Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .healthy { background-color: #d4edda; color: #155724; }
            .error { background-color: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <div class=\"container\">
            <h1>OpenPolicy System Dashboard</h1>
            <div id=\"status\">Loading...</div>
            <h2>Services</h2>
            <div id=\"services\">Loading services...</div>
        </div>
        <script>
            async function checkHealth() {
                try {
                    const response = await fetch(\"http://192.168.2.152:8000/health\");
                    const data = await response.json();
                    document.getElementById(\"status\").innerHTML = 
                        \"<div class=\"status healthy\">✅ API is healthy: \" + JSON.stringify(data) + \"</div>\";
                } catch (error) {
                    document.getElementById(\"status\").innerHTML = 
                        \"<div class=\"status error\">❌ API is not responding: \" + error.message + \"</div>\";
                }
            }
            checkHealth();
            setInterval(checkHealth, 5000);
        </script>
    </body>
    </html>' > /usr/share/nginx/html/index.html
"

echo "✅ Simple deployment completed!"
echo "📊 Services:"
echo "   - API: http://192.168.2.152:8000"
echo "   - Dashboard: http://192.168.2.152:3000"
echo "   - Database: localhost:5432"
echo "   - Redis: localhost:6379"

# Show running containers
echo "📦 Running containers:"
docker ps | grep openpolicy
