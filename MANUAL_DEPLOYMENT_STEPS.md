# Manual Deployment Steps for QNAP Container Station

## 🎯 Current Status
- ✅ QNAP is reachable: http://192.168.2.152
- ✅ Container Station is accessible: http://192.168.2.152:8080/container-station/
- ❌ OpenPolicy system not yet deployed

## 🚀 Step-by-Step Deployment Instructions

### Step 1: Access Container Station

1. **Open your web browser**
2. **Navigate to:** `http://192.168.2.152:8080/container-station/`
3. **Login with:**
   - Username: `ashish101`
   - Password: `Pergola@41`

### Step 2: Create PostgreSQL Database Container

1. **Click "Create" → "Application"**
2. **Search for:** `postgres:15`
3. **Click "Install"**
4. **Configure the container:**
   - **Container name:** `openpolicy_db`
   - **Port mapping:** `5432:5432`
   - **Environment variables:**
     - `POSTGRES_DB=opencivicdata`
     - `POSTGRES_USER=openpolicy`
     - `POSTGRES_PASSWORD=openpolicy123`
5. **Click "Create"**

### Step 3: Create Redis Container

1. **Click "Create" → "Application"**
2. **Search for:** `redis:7-alpine`
3. **Click "Install"**
4. **Configure the container:**
   - **Container name:** `openpolicy_redis`
   - **Port mapping:** `6379:6379`
5. **Click "Create"**

### Step 4: Create FastAPI Backend Container

1. **Click "Create" → "Application"**
2. **Search for:** `python:3.11-slim`
3. **Click "Install"**
4. **Configure the container:**
   - **Container name:** `openpolicy_api`
   - **Port mapping:** `8000:8000`
   - **Environment variables:**
     - `DATABASE_URL=postgresql://openpolicy:openpolicy123@192.168.2.152:5432/opencivicdata`
     - `REDIS_URL=redis://192.168.2.152:6379/0`
     - `CORS_ORIGINS=http://localhost:3000,http://192.168.2.152:3000,http://ashishsnas.myqnapcloud.com`
5. **Click "Create"**

### Step 5: Create Web Dashboard Container

1. **Click "Create" → "Application"**
2. **Search for:** `nginx:alpine`
3. **Click "Install"**
4. **Configure the container:**
   - **Container name:** `openpolicy_dashboard`
   - **Port mapping:** `3000:80`
5. **Click "Create"**

## 🔧 Alternative: Use Docker Compose

If Container Station supports Docker Compose:

1. **Click "Create" → "Docker Compose"**
2. **Copy and paste this configuration:**

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    container_name: openpolicy_db
    environment:
      - POSTGRES_DB=opencivicdata
      - POSTGRES_USER=openpolicy
      - POSTGRES_PASSWORD=openpolicy123
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: openpolicy_redis
    ports:
      - "6379:6379"
    restart: unless-stopped

  api:
    image: python:3.11-slim
    container_name: openpolicy_api
    environment:
      - DATABASE_URL=postgresql://openpolicy:openpolicy123@db:5432/opencivicdata
      - REDIS_URL=redis://redis:6379/0
      - CORS_ORIGINS=http://localhost:3000,http://192.168.2.152:3000,http://ashishsnas.myqnapcloud.com
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    restart: unless-stopped
    command: >
      bash -c "
        apt-get update && apt-get install -y curl &&
        pip install fastapi uvicorn psycopg2-binary redis sqlalchemy &&
        echo 'from fastapi import FastAPI; app = FastAPI(); @app.get(\"/health\"); def health(): return {\"status\": \"healthy\"}; @app.get(\"/\"); def root(): return {\"message\": \"OpenPolicy API\"}' > /app/main.py &&
        cd /app && uvicorn main:app --host 0.0.0.0 --port 8000
      "

  dashboard:
    image: nginx:alpine
    container_name: openpolicy_dashboard
    ports:
      - "3000:80"
    depends_on:
      - api
    restart: unless-stopped
```

3. **Click "Create"**

## 🌐 Access URLs After Deployment

### Local Network Access
- **Dashboard:** http://192.168.2.152:3000
- **API Health:** http://192.168.2.152:8000/health
- **API Root:** http://192.168.2.152:8000

### Domain Access (if available)
- **Dashboard:** https://ashishsnas.myqnapcloud.com:3000
- **API Health:** https://ashishsnas.myqnapcloud.com:8000/health

### Container Station Management
- **Container Station UI:** http://192.168.2.152:8080
- **Container Management:** http://192.168.2.152:8080/container-station/

## 🧪 Testing the Deployment

After deployment, test these endpoints:

1. **API Health Check:**
   ```
   http://192.168.2.152:8000/health
   ```
   Should return: `{"status": "healthy"}`

2. **API Root:**
   ```
   http://192.168.2.152:8000
   ```
   Should return: `{"message": "OpenPolicy API"}`

3. **Dashboard:**
   ```
   http://192.168.2.152:3000
   ```
   Should show a web page

## 📊 Monitoring

### Check Container Status
1. Go to Container Station
2. Click on "Container" tab
3. Verify all containers are "Running"

### Check Logs
1. Click on any container
2. Click "Logs" tab
3. Look for any error messages

## 🔍 Troubleshooting

### If containers fail to start:
1. Check if ports are already in use
2. Verify container images are available
3. Check environment variables
4. Review container logs

### If services aren't responding:
1. Wait a few minutes for initialization
2. Check container status in Container Station
3. Verify network connectivity
4. Test individual containers

### If database connection fails:
1. Ensure PostgreSQL container is running
2. Check database credentials
3. Verify port 5432 is accessible
4. Check container logs for errors

## 🎉 Success Indicators

The deployment is successful when:
- ✅ All containers are "Running" in Container Station
- ✅ API health check returns `{"status": "healthy"}`
- ✅ Dashboard is accessible at http://192.168.2.152:3000
- ✅ No error messages in container logs

## 📞 Next Steps

After successful deployment:
1. Test all endpoints
2. Monitor system performance
3. Set up regular backups
4. Configure notifications
5. Plan for full OpenPolicy system deployment

---

**Estimated Time:** 15-30 minutes  
**Difficulty:** Easy  
**Status:** Ready to deploy 