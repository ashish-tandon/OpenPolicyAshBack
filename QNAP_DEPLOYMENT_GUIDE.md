# 🚀 OpenPolicy QNAP Container Station Deployment Guide

## 📋 Prerequisites

1. **QNAP NAS** with Container Station installed
2. **SSH access** to your QNAP (already configured)
3. **Web browser** to access Container Station

## 🔧 Step 1: Access QNAP Container Station

1. **Open your web browser**
2. **Navigate to**: `http://192.168.2.152:8080`
3. **Login** with your QNAP credentials
4. **Go to Container Station**

## 🐳 Step 2: Deploy Using Container Station Web Interface

### Option A: Manual Container Creation

1. **Create PostgreSQL Container**:
   - Click "Create" → "Application"
   - Search for "postgres:17"
   - Set container name: `openpolicy_postgres`
   - Environment variables:
     ```
     POSTGRES_DB=opencivicdata
     POSTGRES_USER=openpolicy
     POSTGRES_PASSWORD=openpolicy123
     POSTGRES_HOST_AUTH_METHOD=trust
     ```
   - Port mapping: `5432:5432`
   - Volume mapping: `/share/Container/openpolicy/postgres_data:/var/lib/postgresql/data`
   - Click "Create"

2. **Create Redis Container**:
   - Click "Create" → "Application"
   - Search for "redis:7-alpine"
   - Set container name: `openpolicy_redis`
   - Port mapping: `6379:6379`
   - Volume mapping: `/share/Container/openpolicy/redis_data:/data`
   - Click "Create"

3. **Create OpenPolicy API Container**:
   - Click "Create" → "Application"
   - Search for "ashishtandon9/openpolicyashback:latest"
   - Set container name: `openpolicy_api`
   - Environment variables:
     ```
     DB_HOST=openpolicy_postgres
     DB_PORT=5432
     DB_NAME=opencivicdata
     DB_USER=openpolicy
     DB_PASSWORD=openpolicy123
     REDIS_URL=redis://openpolicy_redis:6379/0
     CORS_ORIGINS=http://192.168.2.152:3000,http://localhost:3000,https://dashboard-h1ilgrlf8-ashish-tandons-projects.vercel.app
     ```
   - Port mapping: `8000:8000`
   - Volume mappings:
     ```
     /share/Container/openpolicy/regions_report.json:/app/regions_report.json:ro
     /share/Container/openpolicy/scrapers:/app/scrapers:ro
     ```
   - Click "Create"

4. **Create Celery Worker Container**:
   - Click "Create" → "Application"
   - Search for "ashishtandon9/openpolicyashback:latest"
   - Set container name: `openpolicy_worker`
   - Environment variables:
     ```
     DB_HOST=openpolicy_postgres
     DB_PORT=5432
     DB_NAME=opencivicdata
     DB_USER=openpolicy
     DB_PASSWORD=openpolicy123
     CELERY_BROKER_URL=redis://openpolicy_redis:6379/0
     CELERY_RESULT_BACKEND=redis://openpolicy_redis:6379/0
     ```
   - Command: `["celery", "-A", "src.scheduler.tasks", "worker", "--loglevel=info"]`
   - Volume mappings:
     ```
     /share/Container/openpolicy/regions_report.json:/app/regions_report.json:ro
     /share/Container/openpolicy/scrapers:/app/scrapers:ro
     ```
   - Click "Create"

5. **Create Celery Beat Container**:
   - Click "Create" → "Application"
   - Search for "ashishtandon9/openpolicyashback:latest"
   - Set container name: `openpolicy_beat`
   - Environment variables:
     ```
     DB_HOST=openpolicy_postgres
     DB_PORT=5432
     DB_NAME=opencivicdata
     DB_USER=openpolicy
     DB_PASSWORD=openpolicy123
     CELERY_BROKER_URL=redis://openpolicy_redis:6379/0
     CELERY_RESULT_BACKEND=redis://openpolicy_redis:6379/0
     ```
   - Command: `["celery", "-A", "src.scheduler.tasks", "beat", "--loglevel=info"]`
   - Volume mappings:
     ```
     /share/Container/openpolicy/regions_report.json:/app/regions_report.json:ro
     /share/Container/openpolicy/scrapers:/app/scrapers:ro
     ```
   - Click "Create"

6. **Create Flower Monitor Container**:
   - Click "Create" → "Application"
   - Search for "mher/flower:2.0"
   - Set container name: `openpolicy_flower`
   - Environment variables:
     ```
     CELERY_BROKER_URL=redis://openpolicy_redis:6379/0
     FLOWER_PORT=5555
     ```
   - Port mapping: `5555:5555`
   - Click "Create"

### Option B: Import Docker Compose File

1. **Download the docker-compose.yml** from your QNAP server:
   ```bash
   scp ashish101@192.168.2.152:/share/Container/openpolicy/docker-compose.yml ./
   ```

2. **In Container Station**:
   - Click "Create" → "Application"
   - Click "Import from docker-compose.yml"
   - Upload the docker-compose.yml file
   - Click "Create"

## 🚀 Step 3: Start the System

1. **Start containers in order**:
   - Start `openpolicy_postgres` first
   - Start `openpolicy_redis`
   - Start `openpolicy_api`
   - Start `openpolicy_worker`
   - Start `openpolicy_beat`
   - Start `openpolicy_flower`

2. **Verify all containers are running**:
   - Check Container Station dashboard
   - All containers should show "Running" status

## 🌐 Step 4: Test the System

1. **Test API Health**:
   - Open: `http://192.168.2.152:8000/health`
   - Should return: `{"status": "healthy", "service": "OpenPolicy Database API"}`

2. **Test API Documentation**:
   - Open: `http://192.168.2.152:8000/docs`
   - Should show Swagger UI

3. **Test Flower Monitor**:
   - Open: `http://192.168.2.152:5555`
   - Should show Celery task monitoring

## 🔗 Step 5: Connect Vercel Dashboard

Your Vercel dashboard is already configured to connect to:
- **API Base URL**: `http://192.168.2.152:8000`
- **Dashboard**: https://dashboard-h1ilgrlf8-ashish-tandons-projects.vercel.app

## 📊 Step 6: Monitor and Manage

### View Logs
- In Container Station, click on any container
- Go to "Logs" tab to view real-time logs

### Restart Services
- In Container Station, select container
- Click "Restart" button

### Update System
- Stop all containers
- Pull latest images: `ashishtandon9/openpolicyashback:latest`
- Restart containers

## 🛠️ Troubleshooting

### Container Won't Start
1. Check logs in Container Station
2. Verify port mappings (no conflicts)
3. Check volume permissions

### API Not Responding
1. Verify all containers are running
2. Check network connectivity
3. Test individual container health

### Database Issues
1. Check PostgreSQL container logs
2. Verify database credentials
3. Check volume permissions

## 📞 Support

If you encounter issues:
1. Check Container Station logs
2. Verify network connectivity
3. Ensure all required ports are open

## ✅ Success Indicators

- ✅ All containers show "Running" status
- ✅ API responds at `http://192.168.2.152:8000/health`
- ✅ Vercel dashboard loads real data
- ✅ Flower monitor shows active tasks
- ✅ Database contains sample jurisdictions

---

**🎉 Congratulations! Your OpenPolicy system is now running on QNAP!** 