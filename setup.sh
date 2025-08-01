#!/bin/bash

# OpenPolicy Backend Ash Aug 2025 Setup
# Single-command setup for the complete system

set -e

echo "🇨🇦 OpenPolicy Backend Ash Aug 2025 Setup"
echo "=========================================="
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Docker if not present
if ! command_exists docker; then
    echo "🔧 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    echo "✅ Docker installed successfully"
    echo ""
fi

# Setup Docker permissions
echo "🔧 Setting up Docker permissions..."
sudo usermod -aG docker $USER || true

# Start Docker daemon
echo "🔧 Ensuring Docker daemon is running..."
if ! sudo docker info >/dev/null 2>&1; then
    sudo pkill dockerd || true
    sleep 2
    sudo dockerd > /tmp/docker.log 2>&1 &
    echo "   Waiting for Docker to start..."
    
    # Wait up to 30 seconds for Docker to be ready
    for i in {1..30}; do
        if sudo docker info >/dev/null 2>&1; then
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""
    
    if ! sudo docker info >/dev/null 2>&1; then
        echo "❌ Failed to start Docker daemon"
        exit 1
    fi
fi
echo "✅ Docker daemon is running"
echo ""

# Create .env file from .env.example if it doesn't exist
if [ ! -f .env ]; then
    echo "🔧 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ Environment configuration created"
    echo ""
fi

# Stop any existing containers
echo "🔧 Stopping any existing containers..."
sudo docker compose down --remove-orphans || true
echo ""

# Build and start core services
echo "🚀 Building and starting core services..."
echo "   This may take a few minutes for the first build..."
sudo docker compose build --parallel
echo ""

echo "🚀 Starting services..."
sudo docker compose up -d postgres redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
until sudo docker compose exec postgres pg_isready -U openpolicy -d opencivicdata >/dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo ""
echo "✅ Database is ready"

# Start remaining services
echo "🚀 Starting remaining services..."
sudo docker compose up -d

echo ""
echo "⏳ Waiting for services to stabilize..."
sleep 15

# Check service status
echo "📊 Service Status:"
sudo docker compose ps

echo ""
echo "🎉 OpenPolicy Backend Setup Complete!"
echo ""
echo "📋 Available Services:"
echo "   🐘 PostgreSQL Database: localhost:5432"
echo "   🔴 Redis Cache: localhost:6379"
echo "   📊 API (when stable): http://localhost:8000"
echo "   🌺 Flower Monitoring (when stable): http://localhost:5555"
echo ""
echo "🔍 To check service logs:"
echo "   sudo docker compose logs [service_name]"
echo ""
echo "🛠️  To restart services:"
echo "   sudo docker compose restart"
echo ""
echo "🔄 To check status:"
echo "   sudo docker compose ps"
echo ""
echo "✨ The core infrastructure (Database, Redis, Celery) is now running!"
echo "   Some services may need a moment to fully stabilize."