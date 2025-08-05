#!/bin/bash

# 🚀 Quick Deployment Script for OpenPolicy
# Simple one-command deployment to all environments
# Usage: ./deploy-now.sh [version] [options]

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 OpenPolicy Quick Deployment${NC}"
echo "=================================="

# Check if automated pipeline script exists
if [ ! -f "automated-release-pipeline.sh" ]; then
    echo -e "${YELLOW}❌ Automated pipeline script not found!${NC}"
    echo "Please ensure 'automated-release-pipeline.sh' exists in the current directory."
    exit 1
fi

# Make the pipeline script executable
chmod +x automated-release-pipeline.sh

# Parse arguments
VERSION=${1:-$(date +%Y%m%d-%H%M%S)}
SKIP_TESTS=${2:-false}
DRY_RUN=${3:-false}

echo -e "${BLUE}📋 Deployment Configuration:${NC}"
echo "Version: $VERSION"
echo "Skip Tests: $SKIP_TESTS"
echo "Dry Run: $DRY_RUN"
echo ""

# Build command
CMD="./automated-release-pipeline.sh $VERSION"

if [ "$SKIP_TESTS" = "true" ]; then
    CMD="$CMD --skip-tests"
fi

if [ "$DRY_RUN" = "true" ]; then
    CMD="$CMD --dry-run"
fi

echo -e "${BLUE}🔧 Executing: $CMD${NC}"
echo ""

# Execute the pipeline
eval $CMD

echo ""
echo -e "${GREEN}✅ Quick deployment completed!${NC}"
echo ""
echo -e "${BLUE}📊 Next Steps:${NC}"
echo "1. Check the generated deployment report"
echo "2. Monitor application health at:"
echo "   - Local: http://localhost:8000/health"
echo "   - QNAP: http://ashishsnas.myqnapcloud.com:8000/health"
echo "   - Azure: https://openpolicy-api.azurecontainerapps.io/health"
echo "3. Review logs for any issues"
echo "4. Test key functionality" 