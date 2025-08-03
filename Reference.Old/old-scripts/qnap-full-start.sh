#!/bin/bash

echo "🚀 Starting Complete OpenPolicy System on QNAP..."

# Navigate to deployment directory
cd /share/Container/openpolicy

# Build the dashboard
echo "🏗️ Building dashboard..."
./build-dashboard.sh

# Create data directories
echo "📁 Creating data directories..."
mkdir -p postgres_data redis_data

# Start the system using Container Station
echo "📋 Next Steps:"
echo ""
echo "1. Open QNAP Container Station in your web browser:"
echo "   http://192.168.2.152:8080"
echo ""
echo "2. Import the docker-compose file:"
echo "   - Click 'Create' → 'Application'"
echo "   - Click 'Import from docker-compose.yml'"
echo "   - Upload: /share/Container/openpolicy/qnap-full-docker-compose.yml"
echo "   - Click 'Create'"
echo ""
echo "3. Start all containers in this order:"
echo "   - postgres (first)"
echo "   - redis"
echo "   - api"
echo "   - celery_worker"
echo "   - celery_beat"
echo "   - flower"
echo "   - dashboard (last)"
echo ""
echo "4. Test the system:"
echo "   - API: http://192.168.2.152:8000/health"
echo "   - Dashboard: http://192.168.2.152:3000"
echo "   - Flower Monitor: http://192.168.2.152:5555"
echo ""
echo "✅ Setup complete! Follow the steps above to start the system."
