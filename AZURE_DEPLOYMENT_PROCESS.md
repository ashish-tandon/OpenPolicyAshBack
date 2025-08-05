# 🚀 Azure Deployment Process & Checklist

## 📋 Pre-Deployment Checklist

### ✅ Prerequisites Verification
- [ ] Azure CLI installed (`brew install azure-cli`)
- [ ] Docker Desktop running (`open -a Docker`)
- [ ] Azure account logged in (`az login`)
- [ ] Subscription selected (`az account show`)
- [ ] All required providers registered:
  - [ ] Microsoft.ContainerRegistry
  - [ ] Microsoft.ContainerInstance  
  - [ ] Microsoft.App
  - [ ] Microsoft.OperationalInsights

### ✅ Code Preparation
- [ ] All import issues fixed (relative imports → absolute imports)
- [ ] `__init__.py` files created in all packages
- [ ] Dockerfile updated with correct platform (`--platform linux/amd64`)
- [ ] Requirements.txt up to date
- [ ] Environment variables configured

## 🔄 Deployment Process

### Step 1: Infrastructure Setup
```bash
# 1. Create Resource Group
az group create --name openpolicy-rg --location eastus

# 2. Create Container Registry
az acr create --resource-group openpolicy-rg --name openpolicyacr --sku Basic

# 3. Enable admin access to ACR
az acr update -n openpolicyacr --admin-enabled true

# 4. Get ACR credentials
az acr credential show --name openpolicyacr

# 5. Create Container Apps Environment
az containerapp env create --name openpolicy-env --resource-group openpolicy-rg --location eastus --logs-destination none
```

### Step 2: Code Fixes (Always Required)
```bash
# Fix import issues in main.py
sed -i '' 's/from api\./from src.api./g' src/api/main.py
sed -i '' 's/from api\./from src.api./g' src/api/progress_api.py

# Fix relative imports in progress_api.py
sed -i '' 's/from \.\.progress_tracker/from src.progress_tracker/g' src/api/progress_api.py
sed -i '' 's/from \.\.database/from src.database/g' src/api/progress_api.py
sed -i '' 's/from \.\.scrapers/from src.scrapers/g' src/api/progress_api.py

# Fix ScraperManager initialization in phased_loading.py
sed -i '' 's/ScraperManager(self\.session_factory())/ScraperManager()/g' src/phased_loading.py

# Create missing __init__.py files
touch src/api/__init__.py
```

### Step 3: Docker Build & Push
```bash
# Build with correct platform
docker build --platform linux/amd64 -f Dockerfile.api-simple -t openpolicyacr.azurecr.io/openpolicy-api:latest .

# Login to ACR
az acr login --name openpolicyacr

# Push image
docker push openpolicyacr.azurecr.io/openpolicy-api:latest
```

### Step 4: Container App Deployment
```bash
# Deploy Container App
az containerapp create \
    --name openpolicy-api \
    --resource-group openpolicy-rg \
    --environment openpolicy-env \
    --image openpolicyacr.azurecr.io/openpolicy-api:latest \
    --registry-server openpolicyacr.azurecr.io \
    --registry-username openpolicyacr \
    --registry-password "YOUR_ACR_PASSWORD" \
    --target-port 8000 \
    --ingress external \
    --env-vars \
        DATABASE_URL="sqlite:///./openpolicy.db" \
        REDIS_URL="redis://localhost:6379/0" \
        CORS_ORIGINS="https://openpolicy-api.azurecontainerapps.io" \
        NODE_ENV="production" \
    --cpu 1 \
    --memory 2Gi \
    --min-replicas 1 \
    --max-replicas 3
```

## 🔍 Live Container Monitoring

### Method 1: Direct Container Access (Recommended)
```bash
# Get container logs in real-time
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-api --follow

# Get specific number of log lines
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-api --tail 50

# Get logs from specific revision
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-api --revision openpolicy-api--REVISION_NAME
```

### Method 2: Container Status Monitoring
```bash
# Check container status
az containerapp show --resource-group openpolicy-rg --name openpolicy-api --query "properties.runningStatus"

# Check revision status
az containerapp revision list --resource-group openpolicy-rg --name openpolicy-api

# Get container metrics
az monitor metrics list --resource "/subscriptions/YOUR_SUB_ID/resourceGroups/openpolicy-rg/providers/Microsoft.App/containerApps/openpolicy-api" --metric "cpu" --interval PT1M
```

### Method 3: Real-time Health Checks
```bash
# Continuous health monitoring
watch -n 5 'curl -s -o /dev/null -w "%{http_code}" https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/health'

# Test all endpoints
./deployment-verification.sh
```

## 🛠️ Troubleshooting Guide

### Common Issues & Solutions

#### Issue 1: Import Errors
**Symptoms:** `ImportError: attempted relative import beyond top-level package`
**Solution:**
```bash
# Fix all relative imports
find src -name "*.py" -exec sed -i '' 's/from \.\./from src./g' {} \;
find src -name "*.py" -exec sed -i '' 's/from api\./from src.api./g' {} \;
```

#### Issue 2: Container Not Updating
**Symptoms:** Old revision still running after update
**Solution:**
```bash
# Force new revision by deleting and recreating
az containerapp delete --name openpolicy-api --resource-group openpolicy-rg --yes
# Then recreate using Step 4 above
```

#### Issue 3: Platform Mismatch
**Symptoms:** `no child with platform linux/amd64`
**Solution:**
```bash
# Rebuild with correct platform
docker build --platform linux/amd64 -f Dockerfile.api-simple -t openpolicyacr.azurecr.io/openpolicy-api:latest .
```

#### Issue 4: Registry Authentication
**Symptoms:** `UNAUTHORIZED: authentication required`
**Solution:**
```bash
# Enable admin user and get credentials
az acr update -n openpolicyacr --admin-enabled true
az acr credential show --name openpolicyacr
```

## 📊 Deployment Verification

### Automated Verification
```bash
# Run comprehensive verification
./deployment-verification.sh
```

### Manual Verification Checklist
- [ ] Container status: Running
- [ ] Health endpoint: 200 OK
- [ ] API documentation: Accessible
- [ ] Database connectivity: Working
- [ ] All API endpoints: Responding
- [ ] GraphQL endpoint: Functional
- [ ] External connectivity: Working

### Endpoint Testing
```bash
# Test all critical endpoints
curl -f https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/health
curl -f https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/docs
curl -f https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/stats
curl -f https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/jurisdictions
```

## 🔄 Update Process

### For Code Changes
```bash
# 1. Fix imports (if needed)
# 2. Rebuild image
docker build --platform linux/amd64 -f Dockerfile.api-simple -t openpolicyacr.azurecr.io/openpolicy-api:latest .

# 3. Push to registry
docker push openpolicyacr.azurecr.io/openpolicy-api:latest

# 4. Update container app
az containerapp update --name openpolicy-api --resource-group openpolicy-rg --image openpolicyacr.azurecr.io/openpolicy-api:latest

# 5. Monitor deployment
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-api --follow
```

### For Configuration Changes
```bash
# Update environment variables
az containerapp update --name openpolicy-api --resource-group openpolicy-rg --set-env-vars NEW_VAR="new_value"

# Update scaling
az containerapp update --name openpolicy-api --resource-group openpolicy-rg --min-replicas 2 --max-replicas 5
```

## 📈 Monitoring & Maintenance

### Daily Monitoring Commands
```bash
# Check container health
az containerapp show --resource-group openpolicy-rg --name openpolicy-api --query "properties.runningStatus"

# Monitor logs
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-api --tail 20

# Check resource usage
az containerapp show --resource-group openpolicy-rg --name openpolicy-api --query "properties.template.containers[0].resources"
```

### Weekly Maintenance
- [ ] Review container logs for errors
- [ ] Check resource utilization
- [ ] Update dependencies if needed
- [ ] Backup database if applicable
- [ ] Review security settings

## 🚨 Emergency Procedures

### Container Not Starting
```bash
# 1. Check logs immediately
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-api --tail 50

# 2. Check container status
az containerapp show --resource-group openpolicy-rg --name openpolicy-api

# 3. Restart container
az containerapp restart --name openpolicy-api --resource-group openpolicy-rg

# 4. If still failing, redeploy
az containerapp delete --name openpolicy-api --resource-group openpolicy-rg --yes
# Then follow Step 4 deployment process
```

### Performance Issues
```bash
# Scale up resources
az containerapp update --name openpolicy-api --resource-group openpolicy-rg --cpu 2 --memory 4Gi

# Increase replicas
az containerapp update --name openpolicy-api --resource-group openpolicy-rg --min-replicas 2 --max-replicas 5
```

## 📝 Deployment Notes Template

### For Each Deployment
```
Deployment Date: [DATE]
Deployment Version: [VERSION]
Container App: openpolicy-api
Resource Group: openpolicy-rg
Revision: [REVISION_NAME]
FQDN: [FQDN]

Changes Made:
- [ ] Import fixes
- [ ] Code updates
- [ ] Configuration changes
- [ ] Dependencies updated

Issues Encountered:
- [ ] Issue 1: [Description] - [Resolution]
- [ ] Issue 2: [Description] - [Resolution]

Verification Results:
- [ ] Health endpoint: [Status]
- [ ] API endpoints: [Status]
- [ ] Database: [Status]
- [ ] Performance: [Status]

Next Steps:
- [ ] Action 1
- [ ] Action 2
```

## 🔗 Useful Commands Reference

### Container Management
```bash
# List all container apps
az containerapp list --resource-group openpolicy-rg

# Get container app details
az containerapp show --resource-group openpolicy-rg --name openpolicy-api

# Delete container app
az containerapp delete --name openpolicy-api --resource-group openpolicy-rg --yes

# Restart container app
az containerapp restart --name openpolicy-api --resource-group openpolicy-rg
```

### Logging & Monitoring
```bash
# Real-time logs
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-api --follow

# Historical logs
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-api --tail 100

# Logs from specific time
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-api --since 2024-01-01T00:00:00Z
```

### Registry Management
```bash
# List images
az acr repository list --name openpolicyacr

# Delete old images
az acr repository delete --name openpolicyacr --image openpolicy-api:old-tag

# Show registry credentials
az acr credential show --name openpolicyacr
```

---

**📌 Remember:** Always follow this checklist in order, and never skip the import fixes step. The live monitoring commands should be used continuously during deployment to catch issues early. 