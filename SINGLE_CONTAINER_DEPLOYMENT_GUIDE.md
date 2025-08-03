# 🚀 Single-Container OpenPolicy Deployment for QNAP

## 📋 Overview

This deployment uses **one container to rule them all** - a single Docker container that includes:
- ✅ FastAPI API server
- ✅ PostgreSQL database (SQLite for simplicity)
- ✅ Redis server
- ✅ Celery worker and beat scheduler
- ✅ Flower monitoring dashboard
- ✅ Web dashboard
- ✅ All scrapers and data processing

## 🎯 Benefits

- **Simple**: Only one container to manage
- **Reliable**: No inter-container networking issues
- **Easy**: Works with QNAP's Container Station
- **Efficient**: All services in one place
- **Maintainable**: Single point of configuration

## 📦 What's Included

### Services Running in the Container:
1. **API Server** (Port 8000) - FastAPI with GraphQL
2. **Dashboard** (Port 3000) - Web interface
3. **Flower Monitor** (Port 5555) - Celery task monitoring
4. **Redis** (Port 6379) - Message broker
5. **Celery Worker** - Background task processing
6. **Celery Beat** - Scheduled task scheduler

### Data Storage:
- **SQLite Database** - Stored in `/share/Container/openpolicy/data/`
- **Redis Data** - In-memory (persists while container runs)
- **Configuration Files** - Mounted from QNAP storage

## 🚀 Deployment Steps

### Step 1: Access Container Station
1. Open your web browser
2. Go to: `http://192.168.2.152:8080`
3. Login to QNAP Container Station

### Step 2: Create Application
1. Click **"Create"** → **"Application"**
2. Click **"Import from docker-compose.yml"**
3. Upload the file: `/share/Container/openpolicy/docker-compose.yml`
4. Click **"Create"**

### Step 3: Start the Application
1. Find your new OpenPolicy application
2. Click **"Start"**
3. Wait **2-3 minutes** for all services to start

## 🌐 Access Points

After deployment, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| **API** | http://192.168.2.152:8000 | FastAPI with GraphQL |
| **API Docs** | http://192.168.2.152:8000/docs | Interactive API documentation |
| **Dashboard** | http://192.168.2.152:3000 | Web dashboard |
| **Flower Monitor** | http://192.168.2.152:5555 | Task monitoring |
| **Health Check** | http://192.168.2.152:8000/health | API health status |

## 📊 Management Commands

Connect to your QNAP via SSH and run these commands:

```bash
# Check status
ssh ashish101@192.168.2.152 'cd /share/Container/openpolicy && ./qnap-status-single.sh'

# View logs
ssh ashish101@192.168.2.152 'cd /share/Container/openpolicy && ./qnap-logs-single.sh'

# Stop container
ssh ashish101@192.168.2.152 'cd /share/Container/openpolicy && ./qnap-stop-single.sh'

# Start container
ssh ashish101@192.168.2.152 'cd /share/Container/openpolicy && ./qnap-start-single.sh'
```

## 🔧 Configuration

### Environment Variables:
- `DATABASE_URL`: SQLite database location
- `REDIS_URL`: Redis connection string
- `CORS_ORIGINS`: Allowed origins for API
- `ALL_IN_ONE_MODE`: Enables all-in-one mode

### Volumes:
- `/share/Container/openpolicy/data` → `/app/data` (Database)
- `/share/Container/openpolicy/regions_report.json` → `/app/regions_report.json` (Read-only)
- `/share/Container/openpolicy/scrapers` → `/app/scrapers` (Read-only)

## 📈 Expected Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| **Container Startup** | 2-3 minutes | All services starting |
| **Database Init** | 30 seconds | Tables and data setup |
| **API Ready** | 1 minute | FastAPI server ready |
| **First Data Scraping** | 15-30 minutes | Initial data collection |
| **Complete Setup** | 2-4 hours | Full data population |

## 🧪 Testing

### Quick Health Check:
```bash
curl http://192.168.2.152:8000/health
```

### API Documentation:
Visit: http://192.168.2.152:8000/docs

### Dashboard Test:
Visit: http://192.168.2.152:3000

## 🔍 Troubleshooting

### Container Won't Start:
1. Check Container Station logs
2. Verify image exists: `ashishtandon9/openpolicyashback:all-in-one`
3. Ensure ports 8000, 3000, 5555, 6379 are available

### API Not Responding:
1. Wait 2-3 minutes for startup
2. Check container logs
3. Verify health endpoint: `curl http://192.168.2.152:8000/health`

### Dashboard Issues:
1. Check if port 3000 is accessible
2. Verify API is running (dashboard depends on API)
3. Check browser console for errors

## 📊 Monitoring

### Container Status:
- **Running**: All services operational
- **Starting**: Services initializing
- **Stopped**: Container not running
- **Error**: Check logs for issues

### Key Metrics:
- **API Response Time**: Should be < 1 second
- **Database Connections**: Should be stable
- **Task Queue**: Check Flower monitor for pending tasks
- **Memory Usage**: Monitor container resource usage

## 🎯 Success Indicators

✅ **Container Status**: "Running" in Container Station
✅ **API Health**: `curl http://192.168.2.152:8000/health` returns 200
✅ **Dashboard**: Loads at http://192.168.2.152:3000
✅ **Flower Monitor**: Accessible at http://192.168.2.152:5555
✅ **Data Loading**: Statistics show in dashboard

## 🚀 Next Steps

Once deployed and running:
1. **Monitor** the system for 24 hours
2. **Test** all API endpoints
3. **Verify** data scraping is working
4. **Configure** any additional settings
5. **Backup** the data directory regularly

---

**🎉 Congratulations! Your OpenPolicy system is now running in a single, simple container on QNAP!** 