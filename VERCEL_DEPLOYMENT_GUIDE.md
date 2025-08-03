# OpenPolicy Backend Deployment Guide

## 🚨 Important: Deployment Architecture

Since OpenPolicy Backend is a full-stack application with multiple services (PostgreSQL, Redis, Celery, OPA), we need a hybrid deployment approach:

1. **Frontend (React Dashboard)** → Deploy to Vercel ✅
2. **Backend (API + Services)** → Deploy to a container platform (Railway, Render, or AWS) 🔧

## 📦 Part 1: Deploy Frontend to Vercel

### Prerequisites:
- Vercel account (https://vercel.com)
- Vercel CLI: `npm i -g vercel`

### Steps:

1. **Navigate to dashboard directory:**
```bash
cd dashboard
```

2. **Install dependencies:**
```bash
npm install
```

3. **Deploy to Vercel:**
```bash
vercel
```

4. **Follow the prompts:**
- Link to existing project? No
- Which scope? (Select your account)
- Project name: `openpolicy-dashboard`
- In which directory is your code located? `./`
- Override settings? No

5. **Set environment variables in Vercel:**
```bash
# After deployment, set the API URL
vercel env add VITE_API_URL
# Enter your backend API URL (e.g., https://api.openpolicy.com)
```

### Alternative: Deploy via GitHub

1. Push your code to GitHub
2. Import project in Vercel Dashboard
3. Set environment variables:
   - `VITE_API_URL`: Your backend API URL

## 🚀 Part 2: Deploy Backend Services

### Option A: Railway (Recommended for Full Stack)

Railway supports Docker Compose and provides managed PostgreSQL and Redis.

1. **Create Railway account:** https://railway.app

2. **Install Railway CLI:**
```bash
npm install -g @railway/cli
```

3. **Deploy from root directory:**
```bash
railway login
railway init
railway up
```

4. **Add services in Railway dashboard:**
- PostgreSQL (managed)
- Redis (managed)
- API service (from Dockerfile.api)
- Celery Worker (from Dockerfile.worker)
- Celery Beat (from Dockerfile.beat)

### Option B: Render

1. **Create render.yaml in root:**
```yaml
services:
  - type: web
    name: openpolicy-api
    runtime: docker
    dockerfilePath: ./Dockerfile.api
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: openpolicy-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: openpolicy-redis
          type: redis
          property: connectionString

  - type: worker
    name: openpolicy-worker
    runtime: docker
    dockerfilePath: ./Dockerfile.worker
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: openpolicy-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: openpolicy-redis
          type: redis
          property: connectionString

  - type: cron
    name: openpolicy-beat
    runtime: docker
    dockerfilePath: ./Dockerfile.beat
    schedule: "* * * * *"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: openpolicy-db
          property: connectionString

databases:
  - name: openpolicy-db
    plan: standard
    databaseName: opencivicdata
    user: openpolicy

  - name: openpolicy-redis
    type: redis
    plan: standard
```

2. **Deploy:**
- Push to GitHub
- Connect Render to your repository
- Render will auto-deploy based on render.yaml

### Option C: AWS ECS with RDS

For production-grade deployment:

1. **Use AWS Copilot:**
```bash
copilot init
copilot env init --name production
copilot env deploy --name production
copilot app deploy
```

## 🔗 Part 3: Connect Frontend to Backend

After deploying both parts:

1. **Get your backend API URL**
   - Railway: `https://openpolicy-api.up.railway.app`
   - Render: `https://openpolicy-api.onrender.com`
   - AWS: Your ALB URL

2. **Update Vercel environment variable:**
```bash
vercel env add VITE_API_URL production
# Enter your backend URL
```

3. **Redeploy frontend:**
```bash
vercel --prod
```

## 🧪 Part 4: Verify Deployment

1. **Check frontend:**
   - Visit: `https://openpolicy-dashboard.vercel.app`
   - Should load the React app

2. **Check backend:**
   - API Docs: `https://your-backend-url/docs`
   - Health: `https://your-backend-url/health`

3. **Test full flow:**
   - Navigate to Federal MPs page
   - Should load data from backend API

## 🔐 Part 5: Production Checklist

- [ ] Set up custom domain
- [ ] Configure CORS in backend for frontend domain
- [ ] Set up SSL certificates (auto on Vercel/Railway)
- [ ] Configure production database backups
- [ ] Set up monitoring (Sentry, LogRocket)
- [ ] Configure rate limiting
- [ ] Set secure environment variables
- [ ] Enable auto-scaling

## 📝 Environment Variables Reference

### Frontend (Vercel):
- `VITE_API_URL`: Backend API URL

### Backend (Railway/Render):
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: Application secret
- `ALLOWED_HOSTS`: Your domains
- `CORS_ORIGINS`: Frontend URL

## 🚨 Current Limitations

Since the backend requires multiple services (PostgreSQL, Redis, Celery, OPA), Vercel's serverless functions are not suitable. Use one of the container platforms mentioned above for the backend.

## 🎯 Quick Deploy Commands

```bash
# Frontend to Vercel (from dashboard/ directory)
cd dashboard
npm install
vercel --prod

# Backend to Railway (from root directory)
cd ..
railway login
railway init
railway up

# Set environment variables
vercel env add VITE_API_URL production
# Enter your Railway backend URL
```

Your application will be live at:
- Frontend: `https://[your-project].vercel.app`
- Backend: `https://[your-project].railway.app`