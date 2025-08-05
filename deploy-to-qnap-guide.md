# QNAP Container Station Deployment Guide

## Overview
This guide will help you deploy the OpenPolicy system to your QNAP NAS using Container Station's web interface.

## Prerequisites
- QNAP NAS with Container Station installed and running
- Access to QNAP web interface
- Docker Hub account (optional, for pulling pre-built images)

## Step 1: Access Container Station

1. Open your web browser and navigate to:
   ```
   http://192.168.2.152:8080/container-station/
   ```

2. Login with your QNAP credentials:
   - Username: `ashish101`
   - Password: `Pergola@41`

## Step 2: Create Docker Compose Configuration

1. In Container Station, click on **"Create"** or **"Add Container"**

2. Choose **"Application"** or **"Docker Compose"**

3. Copy and paste the following configuration:

```yaml
version: '3.8'

services:
  openpolicy:
    image: ashishtandon/openpolicy-single:latest
    container_name: openpolicy_single
    ports:
      - "80:80"
      - "8000:8000"
      - "3000:3000"
      - "5555:5555"
      - "6379:6379"
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - DATABASE_URL=postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata
      - REDIS_URL=redis://localhost:6379/0
      - CORS_ORIGINS=http://localhost:3000,http://localhost:80,http://192.168.2.152,http://ashishsnas.myqnapcloud.com
      - NODE_ENV=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  postgres_data:
    driver: local
```

## Step 3: Alternative - Search for Image

If the above doesn't work, try searching for the image:

1. Click **"Search"** in Container Station
2. Search for: `ashishtandon/openpolicy-single`
3. Click **"Install"** on the result
4. Configure the following settings:

### Port Mappings:
- **80:80** (Main web interface)
- **8000:8000** (API)
- **3000:3000** (Dashboard)
- **5555:5555** (Flower monitor)
- **6379:6379** (Redis)
- **5432:5432** (PostgreSQL)

### Environment Variables:
- `DATABASE_URL=postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata`
- `REDIS_URL=redis://localhost:6379/0`
- `CORS_ORIGINS=http://localhost:3000,http://localhost:80,http://192.168.2.152,http://ashishsnas.myqnapcloud.com`
- `NODE_ENV=production`

### Volumes:
- `postgres_data:/var/lib/postgresql/data`

## Step 4: Deploy and Monitor

1. Click **"Create"** or **"Deploy"**
2. Wait for the container to start (this may take several minutes)
3. Monitor the container status in Container Station

## Step 5: Verify Deployment

Once deployed, test the following URLs:

### Local Network Access:
- **Main Dashboard:** http://192.168.2.152
- **API Documentation:** http://192.168.2.152:8000/docs
- **Health Check:** http://192.168.2.152:8000/health
- **Flower Monitor:** http://192.168.2.152:5555

### Domain Access (if available):
- **Main Dashboard:** https://ashishsnas.myqnapcloud.com
- **API Documentation:** https://ashishsnas.myqnapcloud.com/api/docs
- **Health Check:** https://ashishsnas.myqnapcloud.com/health

## Troubleshooting

### If the image doesn't exist:
1. We need to build and push the Docker image to Docker Hub first
2. Or use a different base image and build locally on QNAP

### If container fails to start:
1. Check the container logs in Container Station
2. Verify all required ports are available
3. Check if the image exists and is accessible

### If services aren't responding:
1. Wait a few minutes for all services to initialize
2. Check the health endpoint: http://192.168.2.152:8000/health
3. Review container logs for errors

## Services Included

The OpenPolicy system includes:
1. **PostgreSQL Database** - Port 5432
2. **Redis Cache** - Port 6379
3. **FastAPI Backend** - Port 8000
4. **React Dashboard** - Port 3000
5. **Celery Worker** - Background processing
6. **Celery Beat** - Scheduled tasks
7. **Flower Monitor** - Port 5555
8. **Nginx Reverse Proxy** - Port 80

## Next Steps

After successful deployment:
1. Monitor system performance via Container Station
2. Set up regular backups
3. Configure notifications
4. Test all features and functionality

## Support

If you encounter issues:
1. Check Container Station logs
2. Verify network connectivity
3. Ensure all ports are available
4. Contact support if needed 