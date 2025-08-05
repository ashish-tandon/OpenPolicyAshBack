# 🚀 Azure Deployment Guide for OpenPolicy

## 📋 Prerequisites

1. **Azure Account** with active subscription
2. **Azure CLI** installed and configured
3. **Docker** installed locally
4. **Git** for version control

## 🎯 Deployment Options

### Option 1: Azure Container Instances (ACI) - Simple & Quick
### Option 2: Azure Container Apps (ACA) - Managed & Scalable  
### Option 3: Azure Kubernetes Service (AKS) - Enterprise & Scalable
### Option 4: Azure App Service - Web App with Container

## 🚀 Option 1: Azure Container Instances (Recommended for Start)

### Step 1: Prepare Your Environment

```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "your-subscription-id"

# Create resource group
az group create --name openpolicy-rg --location eastus

# Create container registry (optional but recommended)
az acr create --resource-group openpolicy-rg --name openpolicyacr --sku Basic
```

### Step 2: Build and Push Docker Image

```bash
# Login to your container registry
az acr login --name openpolicyacr

# Build the image
docker build -f Dockerfile.single-container -t openpolicyacr.azurecr.io/openpolicy:latest .

# Push to registry
docker push openpolicyacr.azurecr.io/openpolicy:latest
```

### Step 3: Deploy to Azure Container Instances

```bash
# Deploy the container
az container create \
  --resource-group openpolicy-rg \
  --name openpolicy-container \
  --image openpolicyacr.azurecr.io/openpolicy:latest \
  --dns-name-label openpolicy-app \
  --ports 80 8000 3000 5555 \
  --environment-variables \
    DATABASE_URL="postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata" \
    REDIS_URL="redis://localhost:6379/0" \
    CORS_ORIGINS="https://openpolicy-app.eastus.azurecontainer.io,http://localhost:3000" \
    NODE_ENV="production" \
  --memory 4 \
  --cpu 2
```

### Step 4: Access Your Application

```bash
# Get the public IP
az container show --resource-group openpolicy-rg --name openpolicy-container --query ipAddress.ip --output tsv

# Access URLs:
# Main Dashboard: http://openpolicy-app.eastus.azurecontainer.io
# API: http://openpolicy-app.eastus.azurecontainer.io:8000
# Health Check: http://openpolicy-app.eastus.azurecontainer.io:8000/health
```

## 🌟 Option 2: Azure Container Apps (Recommended for Production)

### Step 1: Enable Container Apps

```bash
# Register the Container Apps provider
az provider register --namespace Microsoft.App

# Create Container Apps environment
az containerapp env create \
  --name openpolicy-env \
  --resource-group openpolicy-rg \
  --location eastus
```

### Step 2: Deploy Container App

```bash
# Deploy the main application
az containerapp create \
  --name openpolicy-app \
  --resource-group openpolicy-rg \
  --environment openpolicy-env \
  --image openpolicyacr.azurecr.io/openpolicy:latest \
  --target-port 80 \
  --ingress external \
  --env-vars \
    DATABASE_URL="postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata" \
    REDIS_URL="redis://localhost:6379/0" \
    CORS_ORIGINS="https://openpolicy-app.azurecontainerapps.io" \
    NODE_ENV="production" \
  --cpu 2 \
  --memory 4Gi \
  --min-replicas 1 \
  --max-replicas 3
```

## 🏢 Option 3: Azure Kubernetes Service (AKS)

### Step 1: Create AKS Cluster

```bash
# Create AKS cluster
az aks create \
  --resource-group openpolicy-rg \
  --name openpolicy-aks \
  --node-count 2 \
  --enable-addons monitoring \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group openpolicy-rg --name openpolicy-aks
```

### Step 2: Create Kubernetes Manifests

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openpolicy
spec:
  replicas: 1
  selector:
    matchLabels:
      app: openpolicy
  template:
    metadata:
      labels:
        app: openpolicy
    spec:
      containers:
      - name: openpolicy
        image: openpolicyacr.azurecr.io/openpolicy:latest
        ports:
        - containerPort: 80
        - containerPort: 8000
        - containerPort: 3000
        - containerPort: 5555
        env:
        - name: DATABASE_URL
          value: "postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata"
        - name: REDIS_URL
          value: "redis://localhost:6379/0"
        - name: CORS_ORIGINS
          value: "https://openpolicy-app.azurecontainerapps.io"
        - name: NODE_ENV
          value: "production"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
---
apiVersion: v1
kind: Service
metadata:
  name: openpolicy-service
spec:
  selector:
    app: openpolicy
  ports:
  - name: http
    port: 80
    targetPort: 80
  - name: api
    port: 8000
    targetPort: 8000
  - name: dashboard
    port: 3000
    targetPort: 3000
  - name: flower
    port: 5555
    targetPort: 5555
  type: LoadBalancer
```

### Step 3: Deploy to AKS

```bash
# Apply the deployment
kubectl apply -f k8s-deployment.yaml

# Check status
kubectl get pods
kubectl get services
```

## 🌐 Option 4: Azure App Service

### Step 1: Create App Service Plan

```bash
# Create App Service plan
az appservice plan create \
  --name openpolicy-plan \
  --resource-group openpolicy-rg \
  --sku B2 \
  --is-linux
```

### Step 2: Create Web App

```bash
# Create web app
az webapp create \
  --resource-group openpolicy-rg \
  --plan openpolicy-plan \
  --name openpolicy-webapp \
  --deployment-local-git

# Configure container
az webapp config container set \
  --resource-group openpolicy-rg \
  --name openpolicy-webapp \
  --docker-custom-image-name openpolicyacr.azurecr.io/openpolicy:latest
```

## 🔧 Environment Variables

All deployment options use these environment variables:

```bash
DATABASE_URL=postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=https://your-app-url.azurecontainer.io
NODE_ENV=production
```

## 📊 Monitoring and Management

### Azure Monitor
```bash
# Enable monitoring
az monitor diagnostic-settings create \
  --resource-group openpolicy-rg \
  --resource-type Microsoft.ContainerInstance/containerGroups \
  --resource-name openpolicy-container \
  --name openpolicy-monitoring \
  --workspace openpolicy-workspace
```

### Log Analytics
```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group openpolicy-rg \
  --workspace-name openpolicy-workspace
```

## 🔒 Security Considerations

### Network Security
```bash
# Create Network Security Group
az network nsg create \
  --resource-group openpolicy-rg \
  --name openpolicy-nsg

# Add security rules
az network nsg rule create \
  --resource-group openpolicy-rg \
  --nsg-name openpolicy-nsg \
  --name allow-http \
  --protocol tcp \
  --priority 100 \
  --destination-port-range 80
```

### Managed Identity
```bash
# Enable managed identity for Container Apps
az containerapp identity assign \
  --name openpolicy-app \
  --resource-group openpolicy-rg \
  --system-assigned
```

## 🚀 Quick Deployment Script

Create `deploy-to-azure.sh`:

```bash
#!/bin/bash

# Azure Deployment Script
set -e

# Configuration
RESOURCE_GROUP="openpolicy-rg"
LOCATION="eastus"
ACR_NAME="openpolicyacr"
CONTAINER_NAME="openpolicy-container"

echo "🚀 Starting Azure deployment..."

# Login to Azure
az login

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create container registry
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic

# Login to ACR
az acr login --name $ACR_NAME

# Build and push image
docker build -f Dockerfile.single-container -t $ACR_NAME.azurecr.io/openpolicy:latest .
docker push $ACR_NAME.azurecr.io/openpolicy:latest

# Deploy to Container Instances
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --image $ACR_NAME.azurecr.io/openpolicy:latest \
  --dns-name-label openpolicy-app \
  --ports 80 8000 3000 5555 \
  --environment-variables \
    DATABASE_URL="postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata" \
    REDIS_URL="redis://localhost:6379/0" \
    CORS_ORIGINS="https://openpolicy-app.eastus.azurecontainer.io" \
    NODE_ENV="production" \
  --memory 4 \
  --cpu 2

echo "✅ Deployment completed!"
echo "🌐 Access your app at: https://openpolicy-app.eastus.azurecontainer.io"
```

## 📈 Scaling Options

### Container Instances
```bash
# Scale by creating multiple instances
az container create \
  --resource-group openpolicy-rg \
  --name openpolicy-container-2 \
  --image openpolicyacr.azurecr.io/openpolicy:latest \
  --dns-name-label openpolicy-app-2
```

### Container Apps
```bash
# Scale Container App
az containerapp revision set-mode \
  --name openpolicy-app \
  --resource-group openpolicy-rg \
  --mode multiple \
  --revision-suffix v2
```

### AKS
```bash
# Scale AKS cluster
az aks scale \
  --resource-group openpolicy-rg \
  --name openpolicy-aks \
  --node-count 3
```

## 🛠️ Troubleshooting

### Common Issues

1. **Container won't start**
   ```bash
   # Check logs
   az container logs --resource-group openpolicy-rg --name openpolicy-container
   ```

2. **Image pull issues**
   ```bash
   # Verify ACR access
   az acr show --name openpolicyacr --resource-group openpolicy-rg
   ```

3. **Port access issues**
   ```bash
   # Check container status
   az container show --resource-group openpolicy-rg --name openpolicy-container
   ```

### Health Checks

```bash
# Test API health
curl https://openpolicy-app.eastus.azurecontainer.io:8000/health

# Test dashboard
curl https://openpolicy-app.eastus.azurecontainer.io
```

## 💰 Cost Optimization

### Container Instances
- Use spot instances for non-critical workloads
- Right-size CPU and memory requirements

### Container Apps
- Set appropriate min/max replicas
- Use consumption plan for variable workloads

### AKS
- Use spot node pools
- Enable cluster autoscaler

## 📞 Support

- **Azure Documentation**: https://docs.microsoft.com/azure/
- **Container Instances**: https://docs.microsoft.com/azure/container-instances/
- **Container Apps**: https://docs.microsoft.com/azure/container-apps/
- **AKS**: https://docs.microsoft.com/azure/aks/

---

**🎉 Choose the deployment option that best fits your needs and budget!** 