#!/bin/bash
set -e

# OpenPolicy Merge - Application Startup Script
# Orchestrates all services in a single container using Supervisor

echo "🚀 Starting OpenPolicy Merge Application..."

# =============================================================================
# Environment Setup
# =============================================================================

# Default environment variables
export ENVIRONMENT=${ENVIRONMENT:-production}
export LOG_LEVEL=${LOG_LEVEL:-info}
export API_HOST=${API_HOST:-0.0.0.0}
export API_PORT=${API_PORT:-8000}
export API_WORKERS=${API_WORKERS:-4}

# Development mode detection
DEV_MODE=false
if [ "$1" = "--dev" ] || [ "$ENVIRONMENT" = "development" ]; then
    DEV_MODE=true
    echo "🔧 Running in development mode"
fi

# =============================================================================
# Pre-startup Checks
# =============================================================================

echo "📋 Running pre-startup checks..."

# Wait for database
echo "⏳ Waiting for database connection..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if python -c "
import os
import psycopg
import sys
try:
    conn = psycopg.connect(os.environ.get('DATABASE_URL'))
    conn.close()
    print('✅ Database connection successful')
    sys.exit(0)
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
    "; then
        break
    fi
    
    echo "🔄 Database connection attempt $attempt/$max_attempts failed, retrying..."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Failed to connect to database after $max_attempts attempts"
    exit 1
fi

# Wait for Redis
echo "⏳ Waiting for Redis connection..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if redis-cli -u "${REDIS_URL:-redis://redis:6379/0}" ping > /dev/null 2>&1; then
        echo "✅ Redis connection successful"
        break
    fi
    
    echo "🔄 Redis connection attempt $attempt/$max_attempts failed, retrying..."
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Failed to connect to Redis after $max_attempts attempts"
    exit 1
fi

# =============================================================================
# Database Initialization
# =============================================================================

echo "🗄️ Initializing database..."

# Run database migrations and setup
python -c "
import os
import sys
sys.path.insert(0, '/app')

try:
    from src.database.config import initialize_database
    
    print('📊 Creating database tables and indexes...')
    if initialize_database():
        print('✅ Database initialization completed successfully')
    else:
        print('❌ Database initialization failed')
        sys.exit(1)
        
except Exception as e:
    print(f'❌ Database initialization error: {e}')
    sys.exit(1)
"

# =============================================================================
# Application Setup
# =============================================================================

echo "⚙️ Setting up application components..."

# Create necessary directories
mkdir -p /app/logs/nginx
mkdir -p /app/logs/supervisor
mkdir -p /app/logs/celery
mkdir -p /app/logs/fastapi
mkdir -p /app/data/uploads
mkdir -p /app/data/exports

# Set permissions
chmod 755 /app/logs/nginx
chmod 755 /app/logs/supervisor
chmod 755 /app/logs/celery
chmod 755 /app/logs/fastapi
chmod 755 /app/data/uploads
chmod 755 /app/data/exports

# =============================================================================
# Service Configuration
# =============================================================================

echo "🔧 Configuring services..."

# Generate Nginx configuration
cat > /etc/nginx/sites-available/default << EOF
server {
    listen 80;
    server_name localhost;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Serve static files (React frontend)
    location / {
        root /app/static;
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeout settings
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Health check
    location /health {
        proxy_pass http://localhost:8000/health;
        proxy_set_header Host \$host;
        access_log off;
    }
    
    # WebSocket support (if needed)
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
    
    # API documentation
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_set_header Host \$host;
    }
    
    location /redoc {
        proxy_pass http://localhost:8000/redoc;
        proxy_set_header Host \$host;
    }
    
    location /openapi.json {
        proxy_pass http://localhost:8000/openapi.json;
        proxy_set_header Host \$host;
    }
}
EOF

# Generate Supervisor configuration
cat > /etc/supervisor/supervisord.conf << EOF
[unix_http_server]
file=/tmp/supervisor.sock
chmod=0700

[supervisord]
logfile=/app/logs/supervisor/supervisord.log
logfile_maxbytes=50MB
logfile_backups=10
loglevel=info
pidfile=/tmp/supervisord.pid
nodaemon=true
minfds=1024
minprocs=200
user=app

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///tmp/supervisor.sock

# FastAPI Application
[program:fastapi]
command=uvicorn src.api.main:app --host ${API_HOST} --port ${API_PORT} --workers ${API_WORKERS}
directory=/app
user=app
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/app/logs/fastapi/fastapi.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=PYTHONPATH="/app"

# Celery Worker
[program:celery-worker]
command=celery -A src.workers.celery_app worker --loglevel=info --concurrency=2
directory=/app
user=app
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/app/logs/celery/worker.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=PYTHONPATH="/app"

# Celery Beat (Scheduler)
[program:celery-beat]
command=celery -A src.workers.celery_app beat --loglevel=info --schedule=/app/data/celerybeat-schedule
directory=/app
user=app
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/app/logs/celery/beat.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=PYTHONPATH="/app"

# Flower (Celery Monitoring)
[program:flower]
command=celery -A src.workers.celery_app flower --port=5555 --address=0.0.0.0
directory=/app
user=app
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/app/logs/celery/flower.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=PYTHONPATH="/app"

# Nginx
[program:nginx]
command=nginx -g "daemon off;"
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/app/logs/nginx/nginx.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
EOF

# =============================================================================
# Development Mode Adjustments
# =============================================================================

if [ "$DEV_MODE" = true ]; then
    echo "🔧 Applying development mode configuration..."
    
    # Update FastAPI command for hot reload
    sed -i 's/--workers ${API_WORKERS}/--reload/' /etc/supervisor/supervisord.conf
    
    # Add development tools
    cat >> /etc/supervisor/supervisord.conf << EOF

# Development: File Watcher for Frontend
[program:frontend-dev]
command=npm run dev
directory=/app/src/frontend
user=app
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/app/logs/frontend-dev.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5

# Development: Code Quality Checks
[program:code-checks]
command=bash -c "sleep 30 && python -m pytest tests/ --cov=src --cov-report=html --cov-report=term"
directory=/app
user=app
autostart=true
autorestart=false
redirect_stderr=true
stdout_logfile=/app/logs/code-checks.log
environment=PYTHONPATH="/app"
EOF
fi

# =============================================================================
# Final Startup
# =============================================================================

echo "🎯 All pre-startup checks completed successfully!"
echo "🚀 Starting all services with Supervisor..."

# Show configuration summary
echo "📊 Configuration Summary:"
echo "   Environment: $ENVIRONMENT"
echo "   API Host: $API_HOST"
echo "   API Port: $API_PORT"
echo "   API Workers: $API_WORKERS"
echo "   Development Mode: $DEV_MODE"
echo "   Log Level: $LOG_LEVEL"

# Start Supervisor (this will run all configured services)
exec supervisord -c /etc/supervisor/supervisord.conf