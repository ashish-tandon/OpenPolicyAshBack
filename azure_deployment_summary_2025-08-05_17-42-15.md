# Azure Deployment Summary

**Date**: Tue Aug  5 17:42:15 EDT 2025
**Container App**: openpolicy-app
**Resource Group**: openpolicy-rg
**Environment**: openpolicy-env

## Configuration
- **Image**: openpolicyacr.azurecr.io/openpolicy:latest
- **Platform**: Linux/AMD64
- **CPU**: 2 cores
- **Memory**: 4GB
- **Scaling**: 1-3 replicas
- **Ingress**: External with HTTPS

## URLs
- **Dashboard**: https://openpolicy-app.kindgrass-4bb31d5d.eastus.azurecontainerapps.io
- **API Root**: https://openpolicy-app.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/api
- **Health Check**: https://openpolicy-app.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/health
- **API Documentation**: https://openpolicy-app.kindgrass-4bb31d5d.eastus.azurecontainerapps.io/api/docs

## Environment Variables
- DATABASE_URL: sqlite:///./openpolicy.db
- CORS_ORIGINS: https://openpolicy-app.kindgrass-4bb31d5d.eastus.azurecontainerapps.io
- NODE_ENV: production

## Features
- ✅ Dashboard UI (React + Vite)
- ✅ FastAPI Backend
- ✅ SQLite Database
- ✅ Nginx Reverse Proxy
- ✅ Rate Limiting (In-Memory)
- ✅ HTTPS with SSL
- ✅ Auto-scaling
- ✅ Health Checks

## Notes
- Platform: Linux/AMD64 (explicitly specified for Azure)
- OS Type: Linux (managed by Azure Container Apps)
- HTTPS: Automatically configured with SSL
- Auto-scaling: Enabled (1-3 replicas)
- Redis: Removed (using in-memory rate limiting)
