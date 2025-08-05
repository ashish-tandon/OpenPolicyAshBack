# Azure Deployment Summary

**Deployment Date:** 2025-08-05 15:10:56
**Resource Group:** openpolicy-rg
**Location:** eastus
**Container App:** openpolicy-api
**Environment:** openpolicy-env

## Container Information
- **FQDN:** openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io
- **Revision:** openpolicy-api--79lle5w
- **Status:** Running

## Access URLs
- **Main API:** https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io
- **Health Check:** https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/health
- **API Documentation:** https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/docs
- **Stats:** https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/stats

## Live Monitoring Commands
```bash
# Real-time logs
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-api --follow

# Check status
az containerapp show --resource-group openpolicy-rg --name openpolicy-api --query 'properties.runningStatus'

# Test health endpoint
curl -f https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/health

# Run full verification
./deployment-verification.sh
```

## Management Commands
```bash
# Update container app
az containerapp update --name openpolicy-api --resource-group openpolicy-rg --image openpolicyacr.azurecr.io/openpolicy-api:latest

# Restart container app
az containerapp restart --name openpolicy-api --resource-group openpolicy-rg

# Delete container app
az containerapp delete --name openpolicy-api --resource-group openpolicy-rg --yes
```

