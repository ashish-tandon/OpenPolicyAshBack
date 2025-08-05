# Azure Container Apps Deployment Summary

**Date**: Tue Aug  5 17:33:27 EDT 2025
**Container App**: openpolicy-api
**Resource Group**: openpolicy-rg
**Environment**: openpolicy-env

## Configuration
- **Image**: openpolicyacr.azurecr.io/openpolicy-api:latest
- **Platform**: Linux/AMD64
- **CPU**: 1 core
- **Memory**: 2GB
- **Scaling**: 1-3 replicas
- **Ingress**: External with HTTPS

## URLs
- **API Root**: https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io
- **Health Check**: https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/health
- **API Documentation**: https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/docs

## Environment Variables
- DATABASE_URL: sqlite:///./openpolicy.db
- REDIS_URL: redis://localhost:6379/0
- CORS_ORIGINS: https://openpolicy-api.kindgrass-4bb31d5d.eastus.azurecontainerapps.io
- NODE_ENV: production

## Notes
- Platform: Linux/AMD64 (explicitly specified for Azure)
- OS Type: Linux (managed by Azure Container Apps)
- HTTPS: Automatically configured with SSL
- Auto-scaling: Enabled (1-3 replicas)
