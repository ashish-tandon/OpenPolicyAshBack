#!/bin/bash

# Transfer OpenPolicy to QNAP Server
echo "📤 Transferring OpenPolicy to QNAP Server..."

QNAP_HOST="192.168.2.152"
QNAP_USER="Ashish101"
QNAP_PATH="/share/Container/openpolicy"

echo "🔗 Connecting to QNAP server..."
echo "📁 Target directory: $QNAP_PATH"

# Create a deployment package
echo "📦 Creating deployment package..."
tar -czf openpolicy-qnap.tar.gz \
    qnap-deploy.sh \
    docker-compose.yml \
    requirements.txt \
    src/ \
    scrapers/ \
    regions_report.json \
    init_db.sql \
    Dockerfile.api \
    Dockerfile.worker \
    Dockerfile.beat

echo "📤 Transferring files to QNAP..."
echo "Please run the following commands on your QNAP server:"
echo ""
echo "1. SSH into your QNAP:"
echo "   ssh $QNAP_USER@$QNAP_HOST"
echo ""
echo "2. Create the directory:"
echo "   mkdir -p $QNAP_PATH"
echo ""
echo "3. Transfer the files (from your Mac):"
echo "   scp openpolicy-qnap.tar.gz $QNAP_USER@$QNAP_HOST:$QNAP_PATH/"
echo ""
echo "4. Extract and run on QNAP:"
echo "   cd $QNAP_PATH"
echo "   tar -xzf openpolicy-qnap.tar.gz"
echo "   chmod +x qnap-deploy.sh"
echo "   ./qnap-deploy.sh"
echo "   ./start-openpolicy.sh"
echo ""
echo "🌐 After deployment, your API will be at:"
echo "   http://$QNAP_HOST:8000"
echo ""
echo "🔗 Update Vercel dashboard API base URL to:"
echo "   http://$QNAP_HOST:8000" 