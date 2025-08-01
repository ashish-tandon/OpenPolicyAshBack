# OpenPolicy Backend Ash Aug 2025

A comprehensive, single-command solution for collecting, managing, and analyzing Canadian civic data with a modern architecture.

## 🚀 Quick Start

**Get the core system running with one command:**

```bash
./setup.sh
```

That's it! The script will:
- Install Docker automatically if needed
- Build and start all core services
- Set up the database with proper schema
- Configure all dependencies

## 🌟 What You Get

### ✅ **Working Core Services**
- **PostgreSQL Database**: Complete civic data storage (Port 5432)
- **Redis**: Task queue and caching (Port 6379) 
- **Celery Beat**: Automated scheduling system
- **Celery Worker**: Background task processing
- **API Infrastructure**: RESTful endpoints (Port 8000)

### 🔧 **Current Status**
- ✅ **Database**: Fully operational with schema
- ✅ **Task Scheduling**: Automated scraping system active
- ✅ **Data Storage**: Complete PostgreSQL setup
- ✅ **Infrastructure**: Docker orchestration working
- 🔨 **Dashboard**: Under development (TypeScript build issues)
- 🔨 **GraphQL API**: Schema refinement in progress
- 🔨 **Flower Monitoring**: Configuration updates needed

### 🇨🇦 **Canadian Civic Data Coverage**
- **123 Active Jurisdictions** across Canada
- **Federal Priority**: Parliament of Canada ready
- **14 Provincial/Territorial** governments configured
- **108 Municipal** jurisdictions prepared
- **Automated Data Collection** framework in place

## 🎯 Access Your System

After running `./setup.sh`, you can access:

- **🗄️ Database**: localhost:5432 (opencivicdata/openpolicy/openpolicy123)
- **📡 Redis**: localhost:6379
- **🔧 API Base**: http://localhost:8000 (when fully operational)
- **🌺 Monitoring**: http://localhost:5555 (when configured)

## ✨ Key Features

### 🔥 **One-Command Setup**
- Automatic Docker installation and configuration
- Complete dependency management
- Environment variable generation
- Database schema initialization

### 🏗 **Production-Ready Architecture**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Task Queue    │    │    Database      │    │   Scheduling    │
│                 │    │                  │    │                 │
│ • Celery Worker │───▶│ • PostgreSQL     │◀───│ • Celery Beat   │
│ • Redis Broker  │    │ • Federal Focus  │    │ • Automated     │
│ • Task Results  │    │ • Data Integrity │    │ • Error Recovery│
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                       │                       │
        │               ┌───────────────┐               │
        └──────────────▶│   API Layer   │◀──────────────┘
                        │               │
                        │ • FastAPI     │
                        │ • GraphQL     │
                        │ • OpenAPI     │
                        │ • Rate Limit  │
                        └───────────────┘
```

### 📋 **Data Structure Ready**
- **Representatives**: MPs, MPPs/MLAs, Mayors, Councillors
- **Bills**: Federal (priority), provincial, and municipal legislation
- **Committees**: Standing and special committees with membership
- **Events**: Meetings, votes, readings, legislative activities
- **Votes**: Individual representative voting records

## 🛠 **System Management**

### Start/Stop Services
```bash
# Stop the system
sudo docker compose down

# Restart all services
sudo docker compose restart

# View service status
sudo docker compose ps

# View logs
sudo docker compose logs -f
```

### Database Access
```bash
# Connect to database
psql -h localhost -p 5432 -U openpolicy -d opencivicdata

# Check service health
sudo docker compose exec postgres pg_isready
```

## 🔧 **Configuration**

The system uses a comprehensive `.env` file with all necessary variables:

```bash
# Core system is working with these defaults
DB_HOST=postgres
DB_PORT=5432
DB_NAME=opencivicdata
DB_USER=openpolicy
DB_PASSWORD=openpolicy123

# Redis configuration
REDIS_URL=redis://redis:6379/0

# Security (automatically generated)
JWT_SECRET_KEY=[auto-generated]
```

## 🚀 **Next Steps**

The core infrastructure is operational. To complete the system:

1. **Fix GraphQL Schema**: Resolve type annotation issues
2. **Complete Dashboard**: Fix TypeScript build errors
3. **Configure Flower**: Complete monitoring setup
4. **Initialize Scrapers**: Begin data collection

## 🛠 **Advanced Usage**

### Manual Task Execution
```bash
# Run database initialization
sudo docker compose exec api python manage.py init

# Check service connectivity
sudo docker compose exec api python -c "import redis; r=redis.Redis(host='redis'); print(r.ping())"

# Test database connection
sudo docker compose exec postgres psql -U openpolicy -d opencivicdata -c "SELECT COUNT(*) FROM information_schema.tables;"
```

### Development Commands
```bash
# Rebuild specific service
sudo docker compose build api

# View specific service logs
sudo docker compose logs api

# Enter service shell
sudo docker compose exec api bash
```

## 🔐 **Production Deployment**

For production use, update `.env` with:

```bash
# Generate secure values
ENVIRONMENT=production
DEBUG=false
DB_PASSWORD=[secure-random-password]
JWT_SECRET_KEY=[secure-random-key]
API_KEY_REQUIRED=true
```

## 📊 **System Requirements**

- **Minimum**: 4GB RAM, 2 CPU cores, 10GB storage
- **Recommended**: 8GB RAM, 4 CPU cores, 50GB storage
- **OS**: Linux (tested on Ubuntu), macOS with Docker Desktop
- **Dependencies**: Docker and Docker Compose (auto-installed)

## 🤝 **Contributing**

The core infrastructure is ready for development:

1. **Add Scrapers**: Extend data collection capabilities
2. **Enhance API**: Complete GraphQL implementation
3. **Build Dashboard**: Complete the React frontend
4. **Add Features**: Federal priority monitoring, AI analysis

## 📄 **Technical Details**

- **Python 3.13**: Latest Python with comprehensive dependencies
- **PostgreSQL 17**: Modern database with full civic data schema
- **Redis 7**: High-performance task queue and caching
- **FastAPI**: Modern Python web framework
- **Celery**: Distributed task processing
- **Docker**: Containerized deployment

---

**🇨🇦 OpenPolicy Backend Ash Aug 2025** - The foundation for comprehensive Canadian civic data collection and analysis.

**Core infrastructure operational. Ready for feature development.**
