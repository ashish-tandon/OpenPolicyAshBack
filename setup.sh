#!/bin/bash

# OpenPolicy Database Setup Script
# This script sets up the entire system with a single command

set -e

echo "🇨🇦 OpenPolicy Backend Ash Aug 2025 Setup"
echo "============================="

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating environment configuration..."
    cp .env.example .env
    echo "✅ Environment file created. Please review and update .env as needed."
else
    echo "✅ Environment file already exists."
fi

# Generate secret keys if needed
if ! grep -q "JWT_SECRET_KEY=your_secret_key_here" .env; then
    echo "🔐 Environment already configured."
else
    echo "🔐 Generating secure secret keys..."
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/JWT_SECRET_KEY=your_secret_key_here/JWT_SECRET_KEY=$SECRET_KEY/" .env
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs data backups

# Pull latest images and build
echo "🔨 Building application..."
docker-compose pull
docker-compose build

# Start services
echo "🚀 Starting OpenPolicy Database..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Initialize database
echo "🗄️ Initializing database..."
docker-compose exec -T api python manage.py init

# Run a test scrape to verify everything works
echo "🧪 Running test scrape..."
docker-compose exec -T api python manage.py run --test --max-records 5

echo ""
echo "🎉 OpenPolicy Backend Ash Aug 2025 is now running!"
echo ""
echo "📊 Access the Dashboard: http://localhost:3000"
echo "🔧 API Documentation: http://localhost:8000/docs"
echo "🌺 Flower Monitoring: http://localhost:5555"
echo "🗄️ Database: localhost:5432"
echo ""
echo "📖 For more information, see the README.md file."
echo ""
echo "🔧 To stop the system: docker-compose down"
echo "🔄 To restart: docker-compose restart"
echo "📋 To view logs: docker-compose logs -f"
echo ""
echo "✨ Happy civic data exploring!"