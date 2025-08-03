# 🔍 OpenPolicy QNAP Validation Guide

## 📊 Container Network Details

Based on your Container Station output, your containers are running on subnet **172.29.0.x**:

| Container | Internal IP | External Port | Service |
|-----------|-------------|---------------|---------|
| openpolicy_postgres | 172.29.0.3 | 5432 | PostgreSQL Database |
| openpolicy_redis | 172.29.0.2 | 6379 | Redis Cache |
| openpolicy_flower | 172.29.0.4 | 5555 | Task Monitor |
| openpolicy_worker | 172.29.0.5 | - | Background Worker |
| openpolicy_beat | 172.29.0.7 | - | Task Scheduler |
| openpolicy_dashboard | 172.29.0.8 | 3000 | Web Dashboard |
| openpolicy_api | (missing) | 8000 | REST API |

**Note**: The API container seems to be missing from the list. Let's check if it's running.

## 🚀 Validation Commands

### 1. Check Missing API Container

```bash
# From your Mac, run:
ssh ashish101@192.168.2.152 "docker ps -a | grep api"
```

### 2. Test API Health

```bash
# Test API endpoint
curl -s http://192.168.2.152:8000/health

# Expected response:
# {"status": "healthy", "service": "OpenPolicy Database API"}
```

### 3. Check Database Tables

```bash
# Check if database tables are created
ssh ashish101@192.168.2.152 "docker exec openpolicy_postgres psql -U openpolicy -d opencivicdata -c '\dt'"

# Count jurisdictions
ssh ashish101@192.168.2.152 "docker exec openpolicy_postgres psql -U openpolicy -d opencivicdata -c 'SELECT COUNT(*) FROM ocd_jurisdiction;'"

# Check all tables
ssh ashish101@192.168.2.152 "docker exec openpolicy_postgres psql -U openpolicy -d opencivicdata -c 'SELECT tablename FROM pg_tables WHERE schemaname = '\''public'\'';'"
```

### 4. Test Dashboard Access

```bash
# Open in browser:
http://192.168.2.152:3000

# Or test with curl:
curl -I http://192.168.2.152:3000
```

### 5. Check Redis Connection

```bash
# Test Redis
ssh ashish101@192.168.2.152 "docker exec openpolicy_redis redis-cli ping"
# Expected: PONG

# Check Redis keys
ssh ashish101@192.168.2.152 "docker exec openpolicy_redis redis-cli keys '*'"
```

### 6. Check Celery Workers

```bash
# Check active workers
ssh ashish101@192.168.2.152 "docker exec openpolicy_worker celery -A src.scheduler.tasks inspect active"

# Check registered tasks
ssh ashish101@192.168.2.152 "docker exec openpolicy_worker celery -A src.scheduler.tasks inspect registered"

# Check worker stats
ssh ashish101@192.168.2.152 "docker exec openpolicy_worker celery -A src.scheduler.tasks inspect stats"
```

### 7. Check Flower Monitor

```bash
# Open in browser:
http://192.168.2.152:5555

# Or check with curl:
curl -s http://192.168.2.152:5555/api/workers | jq '.'
```

### 8. View Container Logs

```bash
# API logs (if running)
ssh ashish101@192.168.2.152 "docker logs --tail 50 openpolicy_api"

# Worker logs
ssh ashish101@192.168.2.152 "docker logs --tail 50 openpolicy_worker"

# Database logs
ssh ashish101@192.168.2.152 "docker logs --tail 50 openpolicy_postgres"
```

### 9. Start Missing API Container (if needed)

If the API container is not running:

```bash
# Start the API container
ssh ashish101@192.168.2.152 "docker start openpolicy_api"

# Or recreate it
ssh ashish101@192.168.2.152 "cd /share/Container/openpolicy && docker-compose up -d api"
```

## 📊 Data Scraping Timeline

### Initial Data Load Estimates:

| Data Type | Estimated Time | Records Expected |
|-----------|----------------|------------------|
| **Federal Parliament** | 2-4 hours | ~338 MPs, ~1000s bills |
| **Provincial Legislatures** | 8-12 hours each | ~100-200 MPPs/MLAs per province |
| **Major Cities** | 4-6 hours each | ~20-50 councillors per city |
| **Total Initial Load** | 24-48 hours | ~10,000+ representatives |

### Factors Affecting Speed:
- Network bandwidth
- Source website response times
- Rate limiting (we respect 1-2 second delays)
- Data complexity and validation

### Daily Updates:
- Incremental updates: 2-4 hours
- New bills/events: Real-time
- Representative changes: Daily sync

## 🎯 Quick Validation Checklist

Run these commands in order:

```bash
# 1. Check all containers are running
ssh ashish101@192.168.2.152 "docker ps --format 'table {{.Names}}\t{{.Status}}'"

# 2. Test API
curl -s http://192.168.2.152:8000/health | jq '.'

# 3. Test Dashboard
curl -I http://192.168.2.152:3000 | head -1

# 4. Check database
ssh ashish101@192.168.2.152 "docker exec openpolicy_postgres psql -U openpolicy -d opencivicdata -c 'SELECT COUNT(*) as tables FROM pg_tables WHERE schemaname = '\''public'\'';'"

# 5. Check workers
curl -s http://192.168.2.152:5555/api/workers | jq 'keys'

# 6. Start a test scrape
curl -X POST http://192.168.2.152:8000/scheduling/schedule \
  -H "Content-Type: application/json" \
  -d '{"task_type": "test"}'
```

## 🚨 Troubleshooting

### If API is not responding:
1. Check if container exists: `docker ps -a | grep api`
2. Start it: `docker start openpolicy_api`
3. Check logs: `docker logs openpolicy_api`

### If database is empty:
1. Run initialization: `docker exec openpolicy_postgres psql -U openpolicy -d opencivicdata -f /docker-entrypoint-initdb.d/init_db.sql`
2. Restart API: `docker restart openpolicy_api`

### If workers aren't processing:
1. Check Redis: `docker exec openpolicy_redis redis-cli ping`
2. Restart workers: `docker restart openpolicy_worker openpolicy_beat`
3. Check Flower: http://192.168.2.152:5555

## ✅ Success Indicators

When everything is working correctly:
- ✅ API returns "healthy" status
- ✅ Dashboard loads with statistics
- ✅ Database has ~20+ tables
- ✅ Flower shows active workers
- ✅ Can start scraping tasks from dashboard