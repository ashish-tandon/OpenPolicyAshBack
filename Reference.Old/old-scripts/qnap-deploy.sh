#!/bin/bash

# OpenPolicy QNAP Deployment Script
# This script sets up the complete OpenPolicy system on QNAP server

set -e

echo "🚀 Starting OpenPolicy QNAP Deployment..."
echo "📋 Target: QNAP Server (192.168.2.152)"
echo "👤 User: Ashish101"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Create deployment directory
DEPLOY_DIR="/share/Container/openpolicy"
print_status "Creating deployment directory: $DEPLOY_DIR"
mkdir -p $DEPLOY_DIR
cd $DEPLOY_DIR

# Create docker-compose.yml for QNAP
print_status "Creating docker-compose configuration..."
cat > docker-compose.yml << 'EOF'
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
      - postgres_data:/var/lib/postgresql/data
      - ./init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
    ports:
      - "5432:5432"
    networks:
      - openpolicy_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U openpolicy -d opencivicdata"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis for Celery
  redis:
    image: redis:7-alpine
    container_name: openpolicy_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - openpolicy_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

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
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - openpolicy_network
    volumes:
      - ./regions_report.json:/app/regions_report.json:ro
      - ./scrapers:/app/scrapers:ro
    restart: unless-stopped

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
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - openpolicy_network
    volumes:
      - ./regions_report.json:/app/regions_report.json:ro
      - ./scrapers:/app/scrapers:ro
    restart: unless-stopped
    command: ["celery", "-A", "src.scheduler.tasks", "worker", "--loglevel=info"]

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
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - openpolicy_network
    volumes:
      - ./regions_report.json:/app/regions_report.json:ro
      - ./scrapers:/app/scrapers:ro
    restart: unless-stopped
    command: ["celery", "-A", "src.scheduler.tasks", "beat", "--loglevel=info"]

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
    networks:
      - openpolicy_network
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  openpolicy_network:
    driver: bridge
EOF

# Create init_db.sql
print_status "Creating database initialization script..."
cat > init_db.sql << 'EOF'
-- OpenPolicy Database Initialization
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create jurisdictions table
CREATE TABLE IF NOT EXISTS jurisdictions (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    jurisdiction_type VARCHAR(50) NOT NULL CHECK (jurisdiction_type IN ('federal', 'provincial', 'municipal')),
    province VARCHAR(10),
    url TEXT,
    api_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create representatives table
CREATE TABLE IF NOT EXISTS representatives (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(100) NOT NULL,
    party VARCHAR(255),
    district VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    jurisdiction_id VARCHAR(255) REFERENCES jurisdictions(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create bills table
CREATE TABLE IF NOT EXISTS bills (
    id VARCHAR(255) PRIMARY KEY,
    identifier VARCHAR(100) NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    status VARCHAR(100),
    jurisdiction_id VARCHAR(255) REFERENCES jurisdictions(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create committees table
CREATE TABLE IF NOT EXISTS committees (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    committee_type VARCHAR(100),
    jurisdiction_id VARCHAR(255) REFERENCES jurisdictions(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create events table
CREATE TABLE IF NOT EXISTS events (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    event_type VARCHAR(100),
    date TIMESTAMP WITH TIME ZONE,
    jurisdiction_id VARCHAR(255) REFERENCES jurisdictions(id),
    bill_id VARCHAR(255) REFERENCES bills(id),
    committee_id VARCHAR(255) REFERENCES committees(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create votes table
CREATE TABLE IF NOT EXISTS votes (
    id VARCHAR(255) PRIMARY KEY,
    vote_type VARCHAR(50) NOT NULL,
    result VARCHAR(50),
    event_id VARCHAR(255) REFERENCES events(id),
    bill_id VARCHAR(255) REFERENCES bills(id),
    representative_id VARCHAR(255) REFERENCES representatives(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_jurisdictions_type ON jurisdictions(jurisdiction_type);
CREATE INDEX IF NOT EXISTS idx_jurisdictions_province ON jurisdictions(province);
CREATE INDEX IF NOT EXISTS idx_representatives_jurisdiction ON representatives(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_representatives_party ON representatives(party);
CREATE INDEX IF NOT EXISTS idx_bills_jurisdiction ON bills(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_bills_status ON bills(status);
CREATE INDEX IF NOT EXISTS idx_events_jurisdiction ON events(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_votes_event ON votes(event_id);

-- Insert sample federal jurisdiction
INSERT INTO jurisdictions (id, name, jurisdiction_type, url, api_url) 
VALUES ('federal-parliament', 'Parliament of Canada', 'federal', 'https://www.parl.ca', 'https://api.parliament.ca')
ON CONFLICT (id) DO NOTHING;

-- Insert sample provincial jurisdiction
INSERT INTO jurisdictions (id, name, jurisdiction_type, province, url, api_url) 
VALUES ('ontario-legislature', 'Legislative Assembly of Ontario', 'provincial', 'ON', 'https://www.ola.org', 'https://api.ola.org')
ON CONFLICT (id) DO NOTHING;

-- Insert sample municipal jurisdiction
INSERT INTO jurisdictions (id, name, jurisdiction_type, province, url, api_url) 
VALUES ('toronto-city', 'City of Toronto', 'municipal', 'ON', 'https://www.toronto.ca', 'https://api.toronto.ca')
ON CONFLICT (id) DO NOTHING;
EOF

# Create regions report
print_status "Creating regions report..."
cat > regions_report.json << 'EOF'
{
  "total_jurisdictions": 123,
  "federal_jurisdictions": 1,
  "provincial_jurisdictions": 14,
  "municipal_jurisdictions": 108,
  "regions": [
    {
      "name": "Federal",
      "jurisdictions": [
        {
          "id": "federal-parliament",
          "name": "Parliament of Canada",
          "type": "federal",
          "url": "https://www.parl.ca"
        }
      ]
    },
    {
      "name": "Ontario",
      "jurisdictions": [
        {
          "id": "ontario-legislature",
          "name": "Legislative Assembly of Ontario",
          "type": "provincial",
          "url": "https://www.ola.org"
        },
        {
          "id": "toronto-city",
          "name": "City of Toronto",
          "type": "municipal",
          "url": "https://www.toronto.ca"
        }
      ]
    }
  ]
}
EOF

# Create scrapers directory
print_status "Creating scrapers directory..."
mkdir -p scrapers

# Create a simple test scraper
cat > scrapers/test_scraper.py << 'EOF'
#!/usr/bin/env python3
"""
Test scraper for OpenPolicy system
"""

import json
import time
from datetime import datetime

def scrape_federal_data():
    """Scrape federal parliamentary data"""
    return {
        "jurisdiction": "federal-parliament",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "representatives": [
                {
                    "id": "mp-001",
                    "name": "Justin Trudeau",
                    "role": "MP",
                    "party": "Liberal",
                    "district": "Papineau"
                }
            ],
            "bills": [
                {
                    "id": "bill-001",
                    "identifier": "C-123",
                    "title": "An Act to amend the Criminal Code",
                    "status": "first_reading"
                }
            ]
        }
    }

if __name__ == "__main__":
    print("Testing scraper...")
    result = scrape_federal_data()
    print(json.dumps(result, indent=2))
EOF

# Create startup script
print_status "Creating startup script..."
cat > start-openpolicy.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting OpenPolicy System on QNAP..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker on your QNAP."
    exit 1
fi

# Pull latest images
echo "📥 Pulling latest Docker images..."
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

# Show API endpoints
echo ""
echo "🌐 API Endpoints:"
echo "  API: http://192.168.2.152:8000"
echo "  API Docs: http://192.168.2.152:8000/docs"
echo "  Flower Monitor: http://192.168.2.152:5555"
echo "  Database: localhost:5432"
echo ""
echo "✅ OpenPolicy system is running!"
echo "🔗 Connect your Vercel dashboard to: http://192.168.2.152:8000"
EOF

chmod +x start-openpolicy.sh

# Create stop script
print_status "Creating stop script..."
cat > stop-openpolicy.sh << 'EOF'
#!/bin/bash

echo "🛑 Stopping OpenPolicy System..."

# Stop all services
docker-compose down

echo "✅ OpenPolicy system stopped."
EOF

chmod +x stop-openpolicy.sh

# Create status script
print_status "Creating status script..."
cat > status-openpolicy.sh << 'EOF'
#!/bin/bash

echo "📊 OpenPolicy System Status"
echo "=========================="

# Check if containers are running
echo ""
echo "🐳 Container Status:"
docker-compose ps

# Check API health
echo ""
echo "🏥 API Health Check:"
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is healthy"
else
    echo "❌ API is not responding"
fi

# Check database connection
echo ""
echo "🗄️ Database Status:"
if docker exec openpolicy_postgres pg_isready -U openpolicy > /dev/null 2>&1; then
    echo "✅ Database is ready"
else
    echo "❌ Database is not ready"
fi

# Show logs
echo ""
echo "📋 Recent Logs:"
docker-compose logs --tail=10
EOF

chmod +x status-openpolicy.sh

# Create update script
print_status "Creating update script..."
cat > update-openpolicy.sh << 'EOF'
#!/bin/bash

echo "🔄 Updating OpenPolicy System..."

# Stop services
docker-compose down

# Pull latest images
docker pull ashishtandon9/openpolicyashback:latest

# Start services
docker-compose up -d

echo "✅ OpenPolicy system updated!"
EOF

chmod +x update-openpolicy.sh

print_success "Deployment files created successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. Run: ./start-openpolicy.sh"
echo "2. Check status: ./status-openpolicy.sh"
echo "3. View logs: docker-compose logs -f"
echo "4. Stop system: ./stop-openpolicy.sh"
echo "5. Update system: ./update-openpolicy.sh"
echo ""
echo "🌐 After starting, your API will be available at:"
echo "   http://192.168.2.152:8000"
echo ""
echo "🔗 Update your Vercel dashboard API configuration to point to:"
echo "   http://192.168.2.152:8000"
echo ""
print_success "QNAP deployment setup complete!" 