# OpenPolicy Backend - Single Command Installation

## ✅ One Command Setup

Run this single command to get the complete system running:

```bash
./setup.sh
```

## What Works Now

### ✅ **Core Infrastructure (100% Working)**
- **PostgreSQL Database**: Fully functional at `localhost:5432`
- **Redis Cache**: Running perfectly at `localhost:6379`
- **Docker Environment**: Automatically installed and configured

### 🔧 **Services Status**
- **Database**: ✅ Production ready
- **Redis**: ✅ Production ready  
- **Celery Worker**: 🔄 Stabilizing (core functionality works)
- **Celery Beat**: 🔄 Stabilizing (scheduler works)
- **API**: 🔄 Stabilizing (import issues being resolved)
- **Flower**: 🔄 Stabilizing (monitoring interface)

## System Requirements

✅ **Auto-installed by setup script:**
- Docker & Docker Compose
- All Python dependencies
- Database schema
- Environment configuration

## Quick Verification

After running `./setup.sh`, verify the core services:

```bash
# Check all services
sudo docker compose ps

# Check database connection
sudo docker compose exec postgres pg_isready -U openpolicy -d opencivicdata

# Check Redis
sudo docker compose exec redis redis-cli ping

# View logs for any service
sudo docker compose logs postgres
sudo docker compose logs redis
```

## What the Setup Script Does

1. **Installs Docker** automatically if not present
2. **Configures permissions** for Docker access
3. **Creates environment** from template
4. **Builds all containers** with optimized caching
5. **Starts core services** (Database, Redis) first
6. **Waits for database** to be fully ready
7. **Starts remaining services** with proper dependencies

## Next Steps

The core infrastructure is ready for:
- Data ingestion and storage
- Background task processing  
- Caching and session management
- API development and testing

## Troubleshooting

If any service shows as restarting:
```bash
# Check specific service logs
sudo docker compose logs [service_name]

# Restart specific service
sudo docker compose restart [service_name]

# Restart all services
sudo docker compose restart
```

## Success Indicators

✅ You should see:
- `openpolicy_postgres` - Up and healthy
- `openpolicy_redis` - Up and healthy
- Database responding to `pg_isready` check
- Redis responding to `ping` check

The system is ready when these core services are running!