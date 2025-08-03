# OpenPolicy Single Container System

A comprehensive Canadian civic data platform that combines PostgreSQL, Redis, FastAPI, Celery, React Dashboard, and monitoring tools in a single Docker container.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git
- SSH access to QNAP NAS

### One-Command Deployment
```bash
./deploy-all.sh
```

This script will:
1. ✅ Validate code and build Docker image
2. ✅ Test locally
3. ✅ Push to Git repository
4. ✅ Push to Docker Hub
5. ✅ Deploy to QNAP NAS
6. ✅ Monitor deployment health

## 🏗️ Architecture

### Single Container Design
The system runs everything in one container for simplicity and ease of deployment:

- **PostgreSQL** - Database (Port 5432)
- **Redis** - Cache and message broker (Port 6379)
- **FastAPI** - REST API and GraphQL (Port 8000)
- **React Dashboard** - Web interface (Port 3000)
- **Celery Worker** - Background task processing
- **Celery Beat** - Scheduled tasks
- **Flower** - Task monitoring (Port 5555)
- **Nginx** - Reverse proxy and load balancer (Port 80)

### Service Dependencies
```
Nginx (Port 80)
├── API (Port 8000)
├── Dashboard (Port 3000)
└── Flower (Port 5555)

API (Port 8000)
├── PostgreSQL (Port 5432)
└── Redis (Port 6379)

Celery Worker
├── PostgreSQL (Port 5432)
└── Redis (Port 6379)
```

## 📁 Project Structure

```
OpenPolicyAshBack/
├── src/                    # Python backend code
│   ├── api/               # FastAPI endpoints
│   ├── database/          # Database models and config
│   ├── scheduler/         # Celery tasks
│   └── scrapers/          # Data scraping modules
├── dashboard/             # React frontend
│   ├── src/              # React components
│   └── package.json      # Node.js dependencies
├── policies/             # OpenPolicy rules
├── scrapers/             # Data scraping scripts
├── Dockerfile.single-container  # Single container build
├── docker-compose.single.yml    # Local development
├── deploy-all.sh         # Complete deployment script
├── monitor-system.sh     # System monitoring
└── nginx.conf           # Nginx configuration
```

## 🔧 Configuration

### Environment Variables
```bash
DATABASE_URL=postgresql://openpolicy:openpolicy123@localhost:5432/opencivicdata
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:3000,http://localhost:80,http://ashishsnas.myqnapcloud.com
NODE_ENV=production
```

### Ports
- **80** - Main entry point (Nginx)
- **8000** - API (direct access)
- **3000** - Dashboard (direct access)
- **5555** - Flower monitor
- **6379** - Redis (direct access)
- **5432** - PostgreSQL (direct access)

## 🚀 Deployment

### Local Development
```bash
# Build and run locally
docker-compose -f docker-compose.single.yml up --build

# Access the application
# Dashboard: http://localhost
# API Docs: http://localhost/api/docs
# Health: http://localhost/health
```

### Production Deployment
```bash
# Complete deployment to all targets
./deploy-all.sh

# Or deploy step by step:
# 1. Build image
docker build -f Dockerfile.single-container -t ashishtandon/openpolicy-single:latest .

# 2. Push to Docker Hub
docker push ashishtandon/openpolicy-single:latest

# 3. Deploy to QNAP
ssh admin@ashishsnas.myqnapcloud.com "docker pull ashishtandon/openpolicy-single:latest"
```

## 📊 Monitoring

### System Health Check
```bash
./monitor-system.sh
```

This script checks:
- ✅ Container status
- ✅ All endpoints
- ✅ Database connectivity
- ✅ System resources
- ✅ Recent logs
- ✅ Auto-restart if needed

### Manual Health Checks
```bash
# API Health
curl https://ashishsnas.myqnapcloud.com/health

# Dashboard
curl https://ashishsnas.myqnapcloud.com/

# Database Stats
curl https://ashishsnas.myqnapcloud.com/api/stats

# Flower Monitor
curl https://ashishsnas.myqnapcloud.com:5555
```

## 🔍 API Endpoints

### Core Endpoints
- `GET /health` - System health check
- `GET /api/stats` - Database statistics
- `GET /api/docs` - API documentation

### Data Endpoints
- `GET /api/jurisdictions` - List jurisdictions
- `GET /api/representatives` - List representatives
- `GET /api/bills` - List bills
- `GET /api/committees` - List committees
- `GET /api/events` - List events
- `GET /api/votes` - List votes

### GraphQL
- `POST /graphql` - GraphQL endpoint

### AI Features
- `POST /api/ai/analyze-bill/{bill_id}` - Analyze bill
- `POST /api/ai/federal-briefing` - Generate federal briefing
- `POST /api/enrich/bill/{bill_id}` - Enrich bill data

## 🛠️ Development

### Adding New Features
1. **Backend**: Add to `src/api/` for new endpoints
2. **Frontend**: Add to `dashboard/src/` for new UI components
3. **Database**: Update `src/database/models.py` for new tables
4. **Tasks**: Add to `src/scheduler/tasks.py` for background jobs

### Testing
```bash
# Run comprehensive tests
python run_comprehensive_tests.py

# Test specific components
python test_system.py
python test_scrapers.py
```

### Logs
```bash
# View container logs
docker logs openpolicy_single

# View specific service logs
docker exec openpolicy_single tail -f /var/log/supervisor/api.log
docker exec openpolicy_single tail -f /var/log/supervisor/dashboard.log
```

## 🔒 Security

### Rate Limiting
- API: 10 requests/second
- Dashboard: 30 requests/second

### CORS Configuration
- Configured for localhost and QNAP domain
- Secure headers enabled

### Database Security
- PostgreSQL with authentication
- Redis with default security

## 📈 Performance

### Optimization Features
- Nginx reverse proxy with gzip compression
- Redis caching layer
- Database connection pooling
- Static asset caching
- Rate limiting

### Resource Usage
- **Memory**: ~2GB (PostgreSQL + Redis + Applications)
- **CPU**: 2-4 cores recommended
- **Storage**: 10GB+ for database and logs

## 🆘 Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check logs
docker logs openpolicy_single

# Check health
./monitor-system.sh
```

**Database connection issues:**
```bash
# Check PostgreSQL
docker exec openpolicy_single su - postgres -c "pg_isready"

# Check Redis
docker exec openpolicy_single redis-cli ping
```

**API not responding:**
```bash
# Check API logs
docker exec openpolicy_single tail -f /var/log/supervisor/api.log

# Restart services
docker restart openpolicy_single
```

### Recovery Procedures
```bash
# Full system restart
docker stop openpolicy_single
docker rm openpolicy_single
docker-compose -f docker-compose.single.yml up -d

# Database reset (WARNING: Data loss)
docker exec openpolicy_single su - postgres -c "dropdb opencivicdata"
docker exec openpolicy_single su - postgres -c "createdb opencivicdata"
```

## 📞 Support

### Access URLs
- **Production**: https://ashishsnas.myqnapcloud.com/
- **API Docs**: https://ashishsnas.myqnapcloud.com/api/docs
- **Health Check**: https://ashishsnas.myqnapcloud.com/health
- **Flower Monitor**: https://ashishsnas.myqnapcloud.com:5555

### Monitoring
- Run `./monitor-system.sh` for system status
- Check logs in `/var/log/supervisor/`
- Monitor container health with `docker ps`

### Emergency Contacts
- System logs: `docker logs openpolicy_single`
- Health check: `curl https://ashishsnas.myqnapcloud.com/health`
- Restart: `docker restart openpolicy_single`

---

**Last Updated**: $(date +'%Y-%m-%d')
**Version**: 1.0.0
**Status**: Production Ready ✅
