# Azure API Deployment Summary

**Deployment Date:** 2025-08-05 17:22:27
**Resource Group:** openpolicy-rg
**Location:** eastus
**Container Name:** openpolicy-api

## Container Information

- **IP Address:** 172.171.143.36
- **FQDN:** openpolicy-api.eastus.azurecontainer.io
- **Status:** Running

## Access URLs

- **API Root:** http://openpolicy-api.eastus.azurecontainer.io:8000
- **Health Check:** http://openpolicy-api.eastus.azurecontainer.io:8000/health
- **API Documentation:** http://openpolicy-api.eastus.azurecontainer.io:8000/docs

## Services Included

1. **FastAPI Backend** - Port 8000
2. **SQLite Database** - Local file
3. **API endpoints**
4. **Health monitoring**

## Management Commands

```bash
# View logs
az container logs --resource-group openpolicy-rg --name openpolicy-api

# Check status
az container show --resource-group openpolicy-rg --name openpolicy-api

# Stop container
az container stop --resource-group openpolicy-rg --name openpolicy-api

# Start container
az container start --resource-group openpolicy-rg --name openpolicy-api
```

## Next Steps

1. Test the API endpoints
2. Verify the deployment is working
3. Consider adding the dashboard later
4. Set up monitoring and alerts

