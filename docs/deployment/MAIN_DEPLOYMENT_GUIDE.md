# 🚀 OpenPolicy Deployment Guide

## 📋 Quick Start - Choose Your Deployment

| Environment | Use Case | Command | Testing | Monitoring |
|-------------|----------|---------|---------|------------|
| **Local** | Development & Testing | `./scripts/deployment/deploy-local.sh` | ✅ Included | Optional |
| **QNAP** | Home/Office Server | `./scripts/deployment/deploy-qnap.sh` | ✅ Included | Optional |
| **Azure** | Production Cloud | `./scripts/deployment/deploy-azure.sh` | ✅ Included | Optional |
| **All** | Complete Deployment | `./scripts/deployment/deploy-all-environments.sh` | ✅ Included | Optional |

---

## 🧪 Comprehensive Testing & Deployment System

### **New Testing Framework**

Our deployment system now includes comprehensive testing at every stage:

#### **1. Pre-Deployment Tests**
```bash
# Run comprehensive pre-deployment testing
./scripts/testing/run-pre-deployment-tests.sh

# Tests included:
- Code quality checks (linting, security scanning)
- Unit tests for all components
- Integration tests
- Build validation
- Performance benchmarks
```

#### **2. Deployment Validation Tests**
```bash
# Validate deployment success
./scripts/testing/validate-deployment.sh --url <deployment-url> --type <local|qnap|azure>

# Validations:
- Health checks
- API endpoints
- Dashboard functionality
- Database connectivity
- Performance metrics
- Security headers
```

#### **3. Continuous Monitoring**
```bash
# Start continuous monitoring
./scripts/testing/monitor-deployment.sh --url <deployment-url> --type <local|qnap|azure> --interval 60

# Monitoring includes:
- Real-time health checks
- Performance tracking
- Error detection and alerting
- Metrics collection
- Automated reporting
```

---

## 🚀 Deployment Commands

### **Local Deployment**
```bash
# Basic deployment
./scripts/deployment/deploy-local.sh

# With monitoring
./scripts/deployment/deploy-local.sh --enable-monitoring --monitoring-email your@email.com

# Skip testing (not recommended)
./scripts/deployment/deploy-local.sh --no-testing

# Skip specific test phases
./scripts/deployment/deploy-local.sh --skip-pre-tests --skip-post-tests
```

### **QNAP Deployment**
```bash
# Basic deployment (requires QNAP configuration)
./scripts/deployment/deploy-qnap.sh

# With QNAP host configuration
QNAP_HOST=192.168.1.100 QNAP_USER=admin ./scripts/deployment/deploy-qnap.sh

# With monitoring
./scripts/deployment/deploy-qnap.sh --enable-monitoring --monitoring-email your@email.com
```

### **Azure Deployment**
```bash
# Basic deployment
./scripts/deployment/deploy-azure.sh

# Skip build (use existing image)
./scripts/deployment/deploy-azure.sh --skip-build

# With monitoring
./scripts/deployment/deploy-azure.sh --enable-monitoring --monitoring-email your@email.com
```

### **Comprehensive All-Environment Deployment**
```bash
# Deploy to all environments with full testing
./scripts/deployment/deploy-all-environments.sh

# Deploy to specific environments only
./scripts/deployment/deploy-all-environments.sh --local-only
./scripts/deployment/deploy-all-environments.sh --azure-only
./scripts/deployment/deploy-all-environments.sh --qnap-only

# Skip specific environments
./scripts/deployment/deploy-all-environments.sh --no-local --no-qnap

# With QNAP configuration
./scripts/deployment/deploy-all-environments.sh --qnap-host 192.168.1.100 --qnap-user admin

# With monitoring
./scripts/deployment/deploy-all-environments.sh --enable-monitoring --monitoring-email your@email.com

# Skip code repository pushes
./scripts/deployment/deploy-all-environments.sh --no-github --no-dockerhub
```

---

## 🔧 Deployment Process with Testing

### **Phase 1: Pre-Deployment**
1. **Prerequisites Check**
   - Verify required tools (Docker, Git, Azure CLI, etc.)
   - Check required files and dependencies
   - Validate environment configuration

2. **Pre-Deployment Testing**
   - Code quality checks (linting, security scanning)
   - Unit tests for all components
   - Integration tests
   - Build validation
   - Performance benchmarks

3. **Code Repository Management**
   - Commit changes to Git
   - Push to GitHub
   - Build and push Docker images to Docker Hub

### **Phase 2: Deployment**
1. **Environment Setup**
   - Create necessary resources (Azure, QNAP, local)
   - Configure networking and security
   - Set up monitoring and logging

2. **Application Deployment**
   - Deploy containers to target environments
   - Configure environment variables
   - Initialize databases and services

3. **Health Validation**
   - Wait for services to be ready
   - Verify health endpoints
   - Check component connectivity

### **Phase 3: Post-Deployment**
1. **Deployment Validation**
   - Run comprehensive validation tests
   - Verify all API endpoints
   - Test dashboard functionality
   - Check database connectivity

2. **Performance Monitoring**
   - Start continuous monitoring
   - Set up alerting
   - Begin metrics collection

3. **Documentation & Reporting**
   - Generate deployment summaries
   - Create access information
   - Document troubleshooting steps

---

## 📊 Testing & Monitoring Features

### **Automated Testing**
- **Pre-deployment tests**: Code quality, unit tests, integration tests
- **Deployment validation**: Health checks, API testing, functionality verification
- **Performance testing**: Response time measurement, resource usage monitoring
- **Security testing**: Header validation, vulnerability scanning

### **Continuous Monitoring**
- **Health monitoring**: Real-time health checks every 60 seconds
- **Performance tracking**: Response time, throughput, error rate monitoring
- **Alert system**: Email notifications for critical issues
- **Metrics collection**: Historical performance data and trends
- **Log aggregation**: Centralized logging and error tracking

### **Test Reports**
- **Pre-deployment reports**: Code coverage, security scan results, performance benchmarks
- **Deployment validation reports**: Health status, API functionality, component connectivity
- **Monitoring reports**: Uptime statistics, performance trends, alert history

---

## 🌐 Environment-Specific Requirements

### **Local Development (Mac)**
```bash
# Requirements
- Docker Desktop
- Git
- curl

# Network Configuration
- Host: localhost
- Port: 80 (Nginx), 8000 (FastAPI)
- Database: SQLite (file-based)
- Rate Limiting: In-memory
```

### **QNAP Container Station**
```bash
# Requirements
- QNAP NAS with Container Station
- SSH access to QNAP
- Docker support

# Network Configuration
- Host: QNAP IP (192.168.x.x)
- Port: 80 (Nginx), 8000 (FastAPI)
- Database: SQLite (persistent volume)
- Rate Limiting: In-memory
```

### **Azure Container Apps**
```bash
# Requirements
- Azure CLI
- Azure subscription
- Docker

# Network Configuration
- Host: Azure Container Apps FQDN
- Port: 80 (Nginx), 8000 (FastAPI)
- Database: SQLite (ephemeral)
- Rate Limiting: In-memory
- Platform: Linux/AMD64 (required)
```

---

## 🔍 Access URLs

### **Local Environment**
- **Dashboard**: http://localhost
- **API**: http://localhost/api
- **Health**: http://localhost/health
- **Stats**: http://localhost/stats
- **API Docs**: http://localhost/docs

### **QNAP Environment**
- **Dashboard**: http://QNAP_IP
- **API**: http://QNAP_IP/api
- **Health**: http://QNAP_IP/health
- **Stats**: http://QNAP_IP/stats
- **API Docs**: http://QNAP_IP/docs

### **Azure Environment**
- **Dashboard**: https://app-name.region.azurecontainerapps.io
- **API**: https://app-name.region.azurecontainerapps.io/api
- **Health**: https://app-name.region.azurecontainerapps.io/health
- **Stats**: https://app-name.region.azurecontainerapps.io/stats
- **API Docs**: https://app-name.region.azurecontainerapps.io/docs

---

## 🛠️ Management Commands

### **Local Environment**
```bash
# View logs
docker-compose logs -f

# Stop application
docker-compose down

# Restart application
docker-compose restart

# Check status
docker-compose ps

# Run validation tests
./scripts/testing/validate-deployment.sh --url http://localhost --type local
```

### **QNAP Environment**
```bash
# View logs (via SSH)
ssh user@qnap-ip "docker logs openpolicy_qnap"

# Stop application (via SSH)
ssh user@qnap-ip "docker stop openpolicy_qnap"

# Restart application (via SSH)
ssh user@qnap-ip "docker restart openpolicy_qnap"

# Check status (via SSH)
ssh user@qnap-ip "docker ps"
```

### **Azure Environment**
```bash
# View logs
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-app --follow

# Stop application
az containerapp stop --resource-group openpolicy-rg --name openpolicy-app

# Restart application
az containerapp restart --resource-group openpolicy-rg --name openpolicy-app

# Check status
az containerapp show --resource-group openpolicy-rg --name openpolicy-app

# Run validation tests
./scripts/testing/validate-deployment.sh --url https://app-url --type azure
```

---

## 📈 Performance & Resources

### **Resource Requirements**
- **CPU**: 2 cores minimum
- **Memory**: 4GB minimum
- **Storage**: 8GB minimum
- **Network**: Standard HTTP/HTTPS ports

### **Performance Targets**
- **Response Time**: < 2 seconds
- **Uptime**: > 99.9%
- **Error Rate**: < 1%
- **Dashboard Load**: < 3 seconds

### **Scaling**
- **Local**: Single container
- **QNAP**: Single container with resource limits
- **Azure**: Auto-scaling (1-3 replicas)

---

## 🔒 Security Features

### **Built-in Security**
- **HTTPS**: Automatic SSL/TLS (Azure)
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
- **Rate Limiting**: In-memory rate limiting (1000 requests/hour)
- **Input Validation**: Comprehensive API input validation
- **Error Handling**: Secure error responses

### **Network Security**
- **Firewall**: Environment-specific firewall rules
- **Access Control**: Environment-specific access controls
- **Monitoring**: Security event monitoring and alerting

---

## 🚨 Troubleshooting

### **Common Issues**

#### **Health Check Failures**
```bash
# Check container status
docker ps  # Local
ssh user@qnap-ip "docker ps"  # QNAP
az containerapp show --resource-group openpolicy-rg --name openpolicy-app  # Azure

# View logs
docker logs openpolicy_local  # Local
ssh user@qnap-ip "docker logs openpolicy_qnap"  # QNAP
az containerapp logs show --resource-group openpolicy-rg --name openpolicy-app  # Azure
```

#### **API Endpoint Issues**
```bash
# Test health endpoint
curl -f http://localhost/health  # Local
curl -f http://qnap-ip/health  # QNAP
curl -f https://azure-url/health  # Azure

# Run validation tests
./scripts/testing/validate-deployment.sh --url <url> --type <environment>
```

#### **Database Issues**
```bash
# Check database connectivity
curl -f http://localhost/stats  # Local
curl -f http://qnap-ip/stats  # QNAP
curl -f https://azure-url/stats  # Azure
```

### **Performance Issues**
```bash
# Check resource usage
docker stats  # Local
ssh user@qnap-ip "docker stats"  # QNAP
az containerapp show --resource-group openpolicy-rg --name openpolicy-app --query "properties.template.containers[0].resources"  # Azure

# Run performance tests
./scripts/testing/validate-deployment.sh --url <url> --type <environment>
```

---

## 📊 Monitoring & Alerting

### **Monitoring Setup**
```bash
# Start monitoring for any environment
./scripts/testing/monitor-deployment.sh --url <deployment-url> --type <environment> --interval 60 --email your@email.com

# Monitor local environment
./scripts/testing/monitor-deployment.sh --url http://localhost --type local --enable-monitoring

# Monitor Azure environment
./scripts/testing/monitor-deployment.sh --url https://azure-url --type azure --enable-monitoring
```

### **Monitoring Features**
- **Real-time health checks**: Every 60 seconds
- **Performance metrics**: Response times, throughput, error rates
- **Resource monitoring**: CPU, memory, disk usage
- **Alert notifications**: Email alerts for critical issues
- **Historical data**: Performance trends and statistics

### **Monitoring Reports**
- **Uptime statistics**: Service availability percentages
- **Performance trends**: Response time and throughput trends
- **Error analysis**: Error rates and types
- **Resource utilization**: CPU, memory, and disk usage

---

## 🎯 Success Metrics

### **Deployment Success Rate**
- **Target**: > 95%
- **Measurement**: Successful deployments / Total deployments

### **Test Coverage**
- **Target**: > 80%
- **Measurement**: Lines of code covered by tests

### **Performance Metrics**
- **Response Time**: < 2 seconds
- **Uptime**: > 99.9%
- **Error Rate**: < 1%

### **User Experience**
- **Dashboard Load Time**: < 3 seconds
- **API Response Time**: < 1 second
- **Data Accuracy**: 100%

---

## 📚 Additional Resources

### **Documentation**
- [Project Structure](./PROJECT_STRUCTURE.md)
- [Architecture Guide](../architecture/ARCHITECTURE.md)
- [Development Guide](../development/DEVELOPMENT.md)
- [Testing Guide](../testing/TESTING.md)

### **Scripts**
- [Pre-deployment Tests](../../scripts/testing/run-pre-deployment-tests.sh)
- [Deployment Validation](../../scripts/testing/validate-deployment.sh)
- [Monitoring](../../scripts/testing/monitor-deployment.sh)
- [Local Deployment](../../scripts/deployment/deploy-local.sh)
- [QNAP Deployment](../../scripts/deployment/deploy-qnap.sh)
- [Azure Deployment](../../scripts/deployment/deploy-azure.sh)
- [All Environments Deployment](../../scripts/deployment/deploy-all-environments.sh)

### **Support**
- **Issues**: Check troubleshooting section above
- **Logs**: Review deployment and monitoring logs
- **Tests**: Run validation tests for specific issues
- **Documentation**: Refer to architecture and development guides

---

**Status**: ✅ **Production Ready**  
**Last Updated**: August 5, 2025  
**Version**: 2.0 (Comprehensive Testing & Monitoring) 