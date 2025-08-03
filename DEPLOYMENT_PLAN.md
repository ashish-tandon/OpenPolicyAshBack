# OpenPolicy Single Container Deployment Plan

## 🎯 Overview

This document outlines the comprehensive deployment strategy for the OpenPolicy system using a single container approach that consolidates all services (PostgreSQL, Redis, FastAPI, React Dashboard, Celery, Flower, and Nginx) into one Docker container.

## 🏗️ Architecture Summary

### Single Container Benefits
- **Simplified Deployment**: One container to rule them all
- **Reduced Complexity**: No inter-container networking issues
- **Easier Monitoring**: All services in one place
- **Resource Efficiency**: Shared resources and optimized startup
- **Portability**: Easy to move between environments

### Service Stack
```
┌─────────────────────────────────────────────────────────────┐
│                    Single Container                         │
├─────────────────────────────────────────────────────────────┤
│  Nginx (Port 80) - Reverse Proxy & Load Balancer           │
│  ├── FastAPI (Port 8000) - REST API & GraphQL              │
│  ├── React Dashboard (Port 3000) - Web Interface           │
│  └── Flower (Port 5555) - Task Monitor                     │
│                                                             │
│  PostgreSQL (Port 5432) - Database                         │
│  Redis (Port 6379) - Cache & Message Broker                │
│  Celery Worker - Background Task Processing                │
│  Celery Beat - Scheduled Tasks                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Deployment Strategy

### Phase 1: Code Validation & Preparation
1. ✅ **Code Review**: Validate all Python and JavaScript code
2. ✅ **Dependency Check**: Ensure all requirements are met
3. ✅ **Configuration**: Update environment variables and settings
4. ✅ **Documentation**: Update README and deployment guides

### Phase 2: Local Testing
1. ✅ **Docker Build**: Create single container image
2. ✅ **Local Deployment**: Test with docker-compose
3. ✅ **Health Checks**: Verify all services start correctly
4. ✅ **Functionality Test**: Ensure API and dashboard work

### Phase 3: Multi-Platform Deployment
1. **Git Repository**: Commit and push all changes
2. **Docker Hub**: Build and push container image
3. **QNAP NAS**: Deploy to production environment
4. **Monitoring**: Set up health checks and alerts

## 📋 Deployment Checklist

### Pre-Deployment
- [x] Clean up old scripts and configurations
- [x] Organize repository structure
- [x] Update Dockerfile for single container
- [x] Configure nginx reverse proxy
- [x] Update supervisord configuration
- [x] Create comprehensive deployment script
- [x] Create monitoring script
- [x] Update documentation

### Deployment Steps
- [ ] Run `./deploy-all.sh` for complete deployment
- [ ] Verify Git push success
- [ ] Confirm Docker Hub upload
- [ ] Test QNAP deployment
- [ ] Validate all endpoints
- [ ] Check monitoring system

### Post-Deployment
- [ ] Run `./monitor-system.sh` for health check
- [ ] Verify all services are running
- [ ] Test API endpoints
- [ ] Check dashboard functionality
- [ ] Monitor logs for errors
- [ ] Create deployment summary

## 🔧 Configuration Details

### Environment Variables
```bash
DATABASE_URL=postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:3000,http://localhost:80,http://ashishsnas.myqnapcloud.com
NODE_ENV=production
```

### Port Configuration
- **80**: Main entry point (Nginx)
- **8000**: API direct access
- **3000**: Dashboard direct access
- **5555**: Flower monitor
- **6379**: Redis direct access
- **5432**: PostgreSQL direct access

### Service Dependencies
```
PostgreSQL → FastAPI → Nginx
Redis → Celery Worker → FastAPI
React Dashboard → Nginx
Flower → Celery Worker
```

## 📊 Monitoring & Health Checks

### Automated Monitoring
- **Container Health**: Docker health checks
- **Service Status**: Supervisor process monitoring
- **API Endpoints**: Regular health check calls
- **Database**: Connection and query testing
- **System Resources**: Memory, CPU, disk usage

### Manual Monitoring
```bash
# System health
./monitor-system.sh

# Container status
docker ps openpolicy_single

# Service logs
docker logs openpolicy_single

# API health
curl https://ashishsnas.myqnapcloud.com/health
```

## 🛡️ Security Considerations

### Network Security
- **Rate Limiting**: API (10 req/s), Dashboard (30 req/s)
- **CORS**: Configured for specific domains
- **Headers**: Security headers enabled
- **SSL**: HTTPS enforced in production

### Data Security
- **Database**: PostgreSQL with authentication
- **Redis**: Default security with network isolation
- **API**: Rate limiting and input validation
- **Logs**: Secure logging without sensitive data

## 🔄 Rollback Strategy

### Quick Rollback
```bash
# Stop current container
docker stop openpolicy_single

# Pull previous version
docker pull ashishtandon/openpolicy-single:previous_tag

# Restart with previous version
docker-compose up -d
```

### Data Backup
- **Database**: PostgreSQL data volume preserved
- **Configuration**: Environment variables backed up
- **Logs**: Log files archived before updates

## 📈 Performance Optimization

### Resource Allocation
- **Memory**: 2GB minimum, 4GB recommended
- **CPU**: 2 cores minimum, 4 cores recommended
- **Storage**: 10GB minimum for database and logs
- **Network**: Stable internet connection for updates

### Optimization Features
- **Nginx**: Gzip compression and caching
- **Redis**: In-memory caching layer
- **PostgreSQL**: Connection pooling
- **Static Assets**: Browser caching enabled

## 🎯 Success Criteria

### Functional Requirements
- [ ] All services start successfully
- [ ] API responds to health checks
- [ ] Dashboard loads and functions
- [ ] Database connections work
- [ ] Background tasks process correctly
- [ ] Monitoring tools accessible

### Performance Requirements
- [ ] API response time < 2 seconds
- [ ] Dashboard load time < 5 seconds
- [ ] Database queries < 1 second
- [ ] 99% uptime maintained
- [ ] Resource usage within limits

### Security Requirements
- [ ] All endpoints secured
- [ ] Rate limiting active
- [ ] CORS properly configured
- [ ] No sensitive data exposed
- [ ] Logs sanitized

## 📞 Support & Maintenance

### Regular Maintenance
- **Daily**: Health check monitoring
- **Weekly**: Log review and cleanup
- **Monthly**: Security updates and patches
- **Quarterly**: Performance optimization

### Emergency Procedures
- **Service Down**: Automatic restart via supervisor
- **Database Issues**: Connection retry with backoff
- **API Errors**: Rate limiting and error handling
- **Resource Exhaustion**: Resource monitoring and alerts

---

**Deployment Plan Version**: 1.0
**Last Updated**: $(date +'%Y-%m-%d %H:%M:%S')
**Status**: Ready for Execution ✅ 