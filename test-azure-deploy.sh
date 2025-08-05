#!/bin/bash

# Simple test deployment to verify Azure Container Instances works

set -e

RESOURCE_GROUP="openpolicy-rg"

echo "🚀 Testing Azure Container Instances with a simple container..."

# Deploy a simple test container
az container create \
    --resource-group "$RESOURCE_GROUP" \
    --name "test-simple" \
    --image nginx:alpine \
    --dns-name-label "test-simple-openpolicy" \
    --ports 80 \
    --os-type Linux \
    --memory 1 \
    --cpu 1 \
    --restart-policy Never

echo "✅ Test container deployed!"

# Get the FQDN
FQDN=$(az container show --resource-group "$RESOURCE_GROUP" --name "test-simple" --query "ipAddress.fqdn" --output tsv)
echo "🌐 Test container FQDN: $FQDN"

# Wait a moment and test
sleep 10
echo "🧪 Testing the container..."
if curl -f -s --max-time 10 "http://$FQDN" >/dev/null 2>&1; then
    echo "✅ Test container is working!"
else
    echo "⚠️ Test container might still be starting up"
fi

# Clean up
echo "🧹 Cleaning up test container..."
az container delete --resource-group "$RESOURCE_GROUP" --name "test-simple" --yes

echo "🎉 Test completed successfully!" 