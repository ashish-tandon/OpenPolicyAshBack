# 🚀 OpenPolicy Comprehensive Deployment Guide

**Date**: August 5, 2025  
**Version**: 1.0.1  
**Status**: Production Ready

## 📋 Overview

This guide provides complete deployment instructions for the OpenPolicy system across all target environments, including specific OS requirements and platform considerations.

## 🎯 Target Environments

### 1. **Local Development (macOS)**
### 2. **QNAP Container Station (NAS)**
### 3. **Azure Cloud (Container Instances & Container Apps)**

---

## 🐳 Local Docker Deployment (macOS)

### ✅ **Requirements**
- **OS**: macOS (Apple Silicon or Intel)
- **Docker**: Docker Desktop 4.0+
- **Platform**: Auto-detected (ARM64 for Apple Silicon, AMD64 for Intel)

### 🔧 **Deployment Steps**

```bash
# 1. Clone repository
git clone https://github.com/ashish-tandon/OpenPolicyAshBack.git
cd OpenPolicyAshBack

# 2. Deploy with Redis
docker-compose -f docker-compose-simple.yml up -d

# 3. Verify deployment
curl http://localhost:8000/health
```

### 📊 **Configuration**
- **Image**: `ashishtandon9/openpolicyashback:latest`
- **Platform**: Auto-detected (no explicit specification needed)
- **Ports**: 8000 (API), 6379 (Redis)
- **Database**: SQLite (local file)
- **Redis**: Containerized Redis 7-alpine

### ✅ **Success Indicators**
- Health check: `{"status":"healthy","service":"OpenPolicy Database API"}`
- API docs: http://localhost:8000/docs
- Redis connectivity: Functional rate limiting

---

## 🏠 QNAP Container Station Deployment

### ✅ **Requirements**
- **OS**: QNAP QTS (Linux-based)
- **Platform**: ARM64 (QNAP ARM processors)
- **Container Station**: 2.0+
- **Docker**: Built-in with Container Station

### 🔧 **Deployment Steps**

```bash
# 1. SSH to QNAP
ssh admin@ashishsnas.myqnapcloud.com

# 2. Navigate to Container Station
# 3. Use the QNAP deployment script
./qnap-simple-deploy.sh
```

### 📊 **Configuration**
- **Image**: `ashishtandon9/openpolicyashback:latest`
- **Platform**: ARM64 (QNAP native)
- **Ports**: 8000 (API), 6379 (Redis)
- **Database**: SQLite (persistent storage)
- **Redis**: Containerized Redis 7-alpine

### ✅ **Success Indicators**
- Container status: Running in Container Station
- Health check: Responding on QNAP IP
- Persistent data: Survives reboots

---

## ☁️ Azure Cloud Deployment

### 🔧 **Azure Container Instances**

#### ✅ **Requirements**
- **OS**: Linux (explicitly required)
- **Platform**: AMD64 (Azure x86_64)
- **Azure CLI**: 2.0+
- **Subscription**: Active Azure subscription

#### 🔧 **Deployment Steps**

```bash
# 1. Login to Azure
az login

# 2. Deploy to Container Instances
./deploy-azure-basic.sh
```

#### 📊 **Configuration**
- **Image**: `openpolicyacr.azurecr.io/openpolicy-api:latest`
- **Platform**: `linux/amd64` (explicitly specified)
- **OS Type**: Linux (required parameter)
- **Memory**: 2GB
- **CPU**: 1 core
- **Database**: SQLite (container storage)
- **Redis**: Not available (limitation of single container)

#### ⚠️ **Known Issues**
- Redis dependency causes 500 errors
- Single container limitation
- No persistent storage

### 🔧 **Azure Container Apps (Recommended)**

#### ✅ **Requirements**
- **OS**: Linux (managed by Azure)
- **Platform**: AMD64 (Azure x86_64)
- **Azure CLI**: 2.0+
- **Container Apps Extension**: Installed

#### 🔧 **Deployment Steps**

```bash
# 1. Install Container Apps extension
az extension add --name containerapp --upgrade

# 2. Deploy to Container Apps
./deploy-azure-container-apps.sh
```

#### 📊 **Configuration**
- **Image**: `openpolicyacr.azurecr.io/openpolicy-api:latest`
- **Platform**: `linux/amd64` (explicitly specified)
- **OS Type**: Linux (managed by Azure)
- **Memory**: 2GB
- **CPU**: 1 core
- **Scaling**: 1-3 replicas
- **Database**: SQLite (persistent volume)
- **Redis**: Azure Redis Cache (optional)

#### ✅ **Advantages**
- Multi-container support
- Auto-scaling
- HTTPS with SSL
- Better monitoring
- Cost-effective

---

## 🔧 **Platform-Specific Requirements**

### 🍎 **macOS (Local)**
```yaml
# No explicit platform specification needed
# Docker Desktop handles architecture detection
image: ashishtandon9/openpolicyashback:latest
platform: auto-detected
```

### 🏠 **QNAP (ARM64)**
```yaml
# ARM64 platform for QNAP processors
image: ashishtandon9/openpolicyashback:latest
platform: linux/arm64
architecture: ARM64
```

### ☁️ **Azure (AMD64)**
```yaml
# AMD64 platform for Azure x86_64 instances
image: openpolicyacr.azurecr.io/openpolicy-api:latest
platform: linux/amd64
os-type: Linux
architecture: x86_64
```

---

## 📦 **Docker Image Specifications**

### **Multi-Architecture Support**
```bash
# Build for multiple platforms
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ashishtandon9/openpolicyashback:latest .
```

### **Platform-Specific Builds**
```bash
# Azure (AMD64)
docker build --platform linux/amd64 -f Dockerfile.api \
  -t openpolicyacr.azurecr.io/openpolicy-api:latest .

# QNAP (ARM64)
docker build --platform linux/arm64 -f Dockerfile.api \
  -t ashishtandon9/openpolicyashback:latest .

# Local (Auto-detected)
docker build -f Dockerfile.api \
  -t ashishtandon9/openpolicyashback:latest .
```

---

## 🔄 **Deployment Scripts Reference**

### **Local Deployment**
- `docker-compose-simple.yml` - Redis + API setup
- `deploy-now.sh` - Quick local deployment

### **QNAP Deployment**
- `qnap-simple-deploy.sh` - QNAP Container Station
- `qnap-single-container-deploy.sh` - Single container setup

### **Azure Deployment**
- `deploy-azure-basic.sh` - Container Instances (Linux/AMD64)
- `deploy-azure-container-apps.sh` - Container Apps (Linux/AMD64)
- `automated-release-pipeline.sh` - Complete CI/CD pipeline

---

## 🛠️ **Troubleshooting by Platform**

### **macOS Issues**
```bash
# Platform detection issues
docker buildx create --use

# Port conflicts
lsof -i :8000
docker-compose -f docker-compose-simple.yml down
```

### **QNAP Issues**
```bash
# ARM64 compatibility
docker build --platform linux/arm64 .

# Container Station permissions
chmod +x *.sh
```

### **Azure Issues**
```bash
# OS type specification required
az container create --os-type Linux ...

# Platform specification required
docker build --platform linux/amd64 ...

# Container Apps extension
az extension add --name containerapp --upgrade
```

---

## 📈 **Performance Considerations**

### **Resource Requirements**
- **Memory**: 2GB minimum (4GB recommended)
- **CPU**: 1 core minimum (2 cores recommended)
- **Storage**: 1GB for application + data
- **Network**: Standard internet connectivity

### **Platform Performance**
- **macOS**: Best performance (native)
- **QNAP**: Good performance (ARM64 optimized)
- **Azure**: Good performance (x86_64 optimized)

---

## 🔒 **Security Considerations**

### **Local Deployment**
- No external exposure
- Local network only
- Standard Docker security

### **QNAP Deployment**
- NAS security settings
- Network isolation
- Container permissions

### **Azure Deployment**
- Azure security policies
- Network security groups
- Container registry authentication
- SSL/TLS encryption

---

## 💰 **Cost Analysis**

### **Local Development**
- **Cost**: Free (existing hardware)
- **Resources**: Local machine resources

### **QNAP Deployment**
- **Cost**: Free (existing NAS)
- **Resources**: NAS resources

### **Azure Deployment**
- **Container Instances**: ~$30/month
- **Container Apps**: ~$20-50/month (pay-per-use)
- **Container Registry**: ~$5/month
- **Total**: $25-85/month depending on usage

---

## 🎯 **Production Recommendations**

### **Development**
- **Platform**: Local macOS
- **Setup**: Docker Compose with Redis
- **Cost**: Free

### **Testing**
- **Platform**: QNAP Container Station
- **Setup**: Single container deployment
- **Cost**: Free

### **Production**
- **Platform**: Azure Container Apps
- **Setup**: Multi-container with Redis Cache
- **Cost**: $20-50/month
- **Features**: Auto-scaling, monitoring, SSL

---

## 📞 **Support and Maintenance**

### **Monitoring Commands**
```bash
# Local
docker ps
docker logs openpolicy_simple

# QNAP
docker ps
docker logs openpolicy_container

# Azure
az container logs --resource-group openpolicy-rg --name openpolicy-api
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-app
```

### **Update Procedures**
```bash
# Local
docker-compose -f docker-compose-simple.yml pull
docker-compose -f docker-compose-simple.yml up -d

# QNAP
./qnap-simple-deploy.sh

# Azure
./automated-release-pipeline.sh v1.0.2
```

---

**🎉 This comprehensive guide covers all deployment scenarios with platform-specific requirements and considerations!** 