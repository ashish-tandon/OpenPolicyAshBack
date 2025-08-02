# Docker Hub Deployment Guide - OpenPolicy Backend

## 🚀 Pushing to Docker Hub

### Prerequisites
1. Docker Hub account (create at https://hub.docker.com)
2. Docker installed locally
3. Docker Hub repositories created (or they'll be created automatically)

### Step 1: Login to Docker Hub
```bash
docker login
# Enter your Docker Hub username and password
```

### Step 2: Build and Push Images

#### Option A: Use the Automated Script (Recommended)
```bash
# Run the build and push script with your Docker Hub username
./build-and-push-docker.sh yourusername

# Or run without arguments and enter username when prompted
./build-and-push-docker.sh
```

#### Option B: Manual Build and Push
```bash
# Set your Docker Hub username
DOCKER_USER=yourusername

# Build images
docker build -t ${DOCKER_USER}/openpolicy-backend:latest -f Dockerfile .
docker build -t ${DOCKER_USER}/openpolicy-backend-policy-validator:latest -f Dockerfile.policy-validator .
docker build -t ${DOCKER_USER}/openpolicy-backend-celery:latest -f Dockerfile .

# Push images
docker push ${DOCKER_USER}/openpolicy-backend:latest
docker push ${DOCKER_USER}/openpolicy-backend-policy-validator:latest
docker push ${DOCKER_USER}/openpolicy-backend-celery:latest
```

### Step 3: Update Docker Hub Repository

1. Go to https://hub.docker.com/r/yourusername/openpolicy-backend
2. Click "Edit Repository Description"
3. Copy contents from `DOCKERHUB_README.md`
4. Update all instances of `yourusername` with your actual Docker Hub username
5. Save changes

## 📦 Published Images

After successful push, you'll have:
- `yourusername/openpolicy-backend:latest` - Main application
- `yourusername/openpolicy-backend-policy-validator:latest` - Policy validator service
- `yourusername/openpolicy-backend-celery:latest` - Celery worker

## 🌐 Deploying to Production

### Option 1: Using Docker Compose (Recommended)

1. **On your production server, create project directory:**
```bash
mkdir openpolicy-deployment
cd openpolicy-deployment
```

2. **Copy required files:**
- `docker-compose.prod.yml` (created by build script)
- `policies/` directory (with .rego files)
- Create `.env` file

3. **Create production .env file:**
```env
# Security - Use strong passwords!
POSTGRES_PASSWORD=your-very-secure-password-here

# API Keys
OPENAI_API_KEY=sk-your-openai-api-key

# Docker Hub username
DOCKER_HUB_USERNAME=yourusername
```

4. **Update docker-compose.prod.yml:**
Replace `${DOCKER_HUB_USERNAME}` with your actual username in all image references.

5. **Run database migrations:**
```bash
# Start only the database first
docker-compose -f docker-compose.prod.yml up -d postgres

# Wait for it to be ready (about 10 seconds)
sleep 10

# Run migrations
docker-compose -f docker-compose.prod.yml run --rm app python -c "
from src.database.connection import engine
from src.database.models import Base
Base.metadata.create_all(engine)
print('Database initialized!')
"

# Apply parliamentary models migration
docker-compose -f docker-compose.prod.yml run --rm app \
  psql $DATABASE_URL -f migrations/001_add_parliamentary_models.sql
```

6. **Start all services:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

7. **Verify deployment:**
```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f app

# Test API health
curl http://localhost:8000/health
curl http://localhost:8181/health
```

### Option 2: Kubernetes Deployment

1. **Create Kubernetes manifests** (example for main app):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openpolicy-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: openpolicy-backend
  template:
    metadata:
      labels:
        app: openpolicy-backend
    spec:
      containers:
      - name: app
        image: yourusername/openpolicy-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: openpolicy-secrets
              key: database-url
        - name: REDIS_URL
          value: redis://redis-service:6379/0
        - name: OPA_URL
          value: http://opa-service:8181
```

2. **Apply manifests:**
```bash
kubectl apply -f k8s/
```

### Option 3: Cloud Platform Deployment

#### AWS ECS
```bash
# Create task definition using the Docker images
# Deploy using ECS service
```

#### Google Cloud Run
```bash
# Deploy main app
gcloud run deploy openpolicy-backend \
  --image yourusername/openpolicy-backend:latest \
  --platform managed \
  --allow-unauthenticated
```

#### Azure Container Instances
```bash
# Deploy using Azure CLI
az container create \
  --name openpolicy-backend \
  --image yourusername/openpolicy-backend:latest \
  --cpu 2 --memory 4
```

## 🔧 Post-Deployment Steps

### 1. Initialize Data
```bash
# Run initial data population
docker-compose -f docker-compose.prod.yml run --rm app python manage.py populate_db

# Start parliamentary data collection
docker-compose -f docker-compose.prod.yml run --rm app python manage.py scrape --type parliamentary
```

### 2. Configure Monitoring
```bash
# Access Flower for Celery monitoring
http://your-server:5555

# Set up health check monitoring
# Add to your monitoring system:
- http://your-server:8000/health
- http://your-server:8181/health
- http://your-server:8000/api/parliamentary/policy/health
```

### 3. Set Up SSL/TLS
```nginx
# Nginx configuration example
server {
    listen 443 ssl;
    server_name openpolicy.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /opa/ {
        proxy_pass http://localhost:8181/;
    }
}
```

### 4. Configure Backups
```bash
# Database backup script
#!/bin/bash
docker-compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U openpolicy opencivicdata | gzip > backup_$(date +%Y%m%d).sql.gz
```

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# API Health
curl http://localhost:8000/health

# OPA Policy Engine
curl http://localhost:8181/health

# Parliamentary Features
curl http://localhost:8000/api/parliamentary/analytics/summary
```

### Logs
```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs

# Follow specific service
docker-compose -f docker-compose.prod.yml logs -f app

# Check Celery tasks
docker-compose -f docker-compose.prod.yml logs celery-worker
```

### Updates
```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Restart services with zero downtime
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale app=2 app
docker-compose -f docker-compose.prod.yml up -d --no-deps app
```

## 🛡️ Security Recommendations

1. **Use secrets management**:
   - AWS Secrets Manager
   - HashiCorp Vault
   - Kubernetes Secrets

2. **Network isolation**:
   - Use Docker networks
   - Implement firewall rules
   - Use VPN for admin access

3. **Regular updates**:
   - Monitor for security updates
   - Use specific version tags in production
   - Test updates in staging first

4. **Access control**:
   - Implement API gateway
   - Use rate limiting
   - Monitor access logs

## 🆘 Troubleshooting

### Common Issues

1. **Database connection errors**:
```bash
# Check postgres is running
docker-compose -f docker-compose.prod.yml ps postgres

# Check logs
docker-compose -f docker-compose.prod.yml logs postgres
```

2. **OPA policy errors**:
```bash
# Verify policies are loaded
curl http://localhost:8181/v1/data/openpolicy

# Check OPA logs
docker-compose -f docker-compose.prod.yml logs opa
```

3. **Celery task failures**:
```bash
# Check worker status
docker-compose -f docker-compose.prod.yml logs celery-worker

# Access Flower UI
http://localhost:5555
```

## 📞 Support

- GitHub Issues: https://github.com/yourusername/openpolicy-backend/issues
- Documentation: See `/docs` endpoint
- Docker Hub: https://hub.docker.com/r/yourusername/openpolicy-backend

---

Remember to replace `yourusername` with your actual Docker Hub username throughout!