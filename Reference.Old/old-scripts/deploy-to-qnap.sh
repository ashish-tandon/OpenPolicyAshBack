#!/bin/bash

# Deploy OpenPolicy to QNAP Server with SSH Key Authentication
echo "🚀 Deploying OpenPolicy to QNAP Server..."

QNAP_HOST="192.168.2.152"
QNAP_USER="ashish101"
QNAP_PATH="/share/Container/openpolicy"

# Check if SSH key authentication is working
echo "🔑 Testing SSH key authentication..."
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes $QNAP_USER@$QNAP_HOST "echo 'SSH key authentication working'" 2>/dev/null; then
    echo "❌ SSH key authentication failed!"
    echo "Please run: ./setup-ssh-key.sh"
    exit 1
fi

echo "✅ SSH key authentication working!"

# Create deployment directory on QNAP
echo "📁 Creating deployment directory on QNAP..."
ssh $QNAP_USER@$QNAP_HOST "mkdir -p $QNAP_PATH"

# Transfer deployment files
echo "📤 Transferring deployment files..."
scp -r \
    docker-compose.yml \
    requirements.txt \
    src/ \
    scrapers/ \
    regions_report.json \
    init_db.sql \
    Dockerfile.api \
    Dockerfile.worker \
    Dockerfile.beat \
    $QNAP_USER@$QNAP_HOST:$QNAP_PATH/

# Transfer and run deployment script
echo "📤 Transferring deployment script..."
scp qnap-deploy.sh $QNAP_USER@$QNAP_HOST:$QNAP_PATH/

# Execute deployment on QNAP
echo "🔄 Executing deployment on QNAP..."
ssh $QNAP_USER@$QNAP_HOST "cd $QNAP_PATH && chmod +x qnap-deploy.sh && ./qnap-deploy.sh"

# Start the system
echo "🚀 Starting OpenPolicy system..."
ssh $QNAP_USER@$QNAP_HOST "cd $QNAP_PATH && ./start-openpolicy.sh"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Your OpenPolicy API is now running at:"
echo "   http://$QNAP_HOST:8000"
echo ""
echo "📊 Monitor your system:"
echo "   ssh $QNAP_USER@$QNAP_HOST 'cd $QNAP_PATH && ./status-openpolicy.sh'"
echo ""
echo "🔗 Update your Vercel dashboard API configuration to:"
echo "   http://$QNAP_HOST:8000" 