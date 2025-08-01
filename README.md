# OpenPolicy Backend Ash Aug 2025

A comprehensive, single-command solution for collecting, managing, and analyzing Canadian civic data with a beautiful modern web interface.

## 🚀 Quick Start

**Get everything running with one command:**

```bash
./setup.sh
```

That's it! The script will:
- Set up the environment
- Build and start all services
- Initialize the database
- Run a test scrape to verify everything works

## 🌟 What You Get

### 📊 Beautiful Modern Dashboard
- **Real-time Overview**: Statistics, charts, and system health monitoring
- **Database Browser**: Search, filter, and export all civic data
- **Scraper Management**: Schedule and monitor data collection tasks
- **Federal Priority**: Enhanced monitoring for Canadian federal bills
- **Responsive Design**: Works perfectly on desktop and mobile

### 🇨🇦 Comprehensive Data Collection
- **123 Active Jurisdictions** across Canada
- **Federal Priority**: Enhanced monitoring for Parliament of Canada
- **14 Provincial/Territorial** governments
- **108 Municipal** jurisdictions
- **Automated Daily Updates** with smart error recovery

### 🛠 Enterprise Features
- **One-Command Setup**: Complete deployment with `./setup.sh`
- **Beautiful UI**: Modern React dashboard with real-time updates
- **Federal Bills Priority**: Special monitoring for critical legislation
- **Quality Assurance**: Automated spot checks and validation
- **API-First**: Full REST API with Swagger documentation
- **Container-Ready**: Full Docker Compose orchestration

## 🎯 Access Your System

After running `./setup.sh`, access:

- **📊 Dashboard**: http://localhost:3000
- **🔧 API Docs**: http://localhost:8000/docs
- **🌺 Monitoring**: http://localhost:5555
- **🗄️ Database**: localhost:5432

## ✨ Key Features

### 🔥 Federal Bills Priority
The system provides **enhanced monitoring** specifically for Federal Canadian bills:
- ✅ **Automated Quality Checks**: Format validation, status progression
- ✅ **Critical Bill Detection**: Identifies important legislation automatically
- ✅ **Data Freshness Monitoring**: Ensures federal data is always current
- ✅ **Smart Alerts**: Proactive notifications for issues
- ✅ **Priority Scheduling**: More frequent updates for federal data

### 📋 Data Collected
- **Representatives**: MPs, MPPs/MLAs, Mayors, Councillors
- **Bills**: Federal bills with priority monitoring, provincial and municipal legislation
- **Committees**: Standing and special committees with membership
- **Events**: Meetings, votes, readings, legislative activities
- **Votes**: Individual representative voting records

### 🎨 Modern Dashboard Features
- **Interactive Charts**: Visualize data distributions and trends
- **Advanced Filtering**: Search and filter by jurisdiction, party, status
- **Data Export**: CSV export for all data types
- **Real-time Updates**: Live monitoring of scraping tasks
- **Responsive Design**: Beautiful interface on any device
- **Federal Focus**: Special views for priority federal legislation

## 🏗 Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Dashboard     │    │    Database      │    │   Scheduling    │
│                 │    │                  │    │                 │
│ • React UI      │───▶│ • PostgreSQL     │◀───│ • Celery Tasks  │
│ • Real-time     │    │ • Federal Focus  │    │ • Federal Prio  │
│ • Responsive    │    │ • Quality Checks │    │ • Auto Recovery │
│ • Export        │    │ • Validation     │    │ • Smart Alerts  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                       │                       │
        │               ┌───────────────┐               │
        └──────────────▶│   API Layer   │◀──────────────┘
                        │               │
                        │ • FastAPI     │
                        │ • OpenAPI     │
                        │ • Rate Limit  │
                        │ • Auth Ready  │
                        └───────────────┘
```

## 🎛 Dashboard Features

### 📈 Overview Dashboard
- **Key Metrics**: Total jurisdictions, representatives, bills
- **Visual Charts**: Distribution by type, status trends
- **Recent Activity**: Latest updates and changes
- **System Health**: Real-time status monitoring

### 🗃 Database Browser
- **Tabbed Interface**: Jurisdictions, Representatives, Bills
- **Advanced Search**: Text search with smart filtering
- **Export Capability**: CSV download for analysis
- **Detailed Views**: Complete record information

### ⏰ Scheduling Interface
- **Quick Actions**: One-click task scheduling
- **Federal Priority**: Special federal-only scrapers
- **Task Monitoring**: Real-time progress tracking
- **Performance Metrics**: Success rates and timing

### 🔍 Federal Bills Priority
- **Enhanced Monitoring**: Special attention to federal legislation
- **Quality Checks**: Automated validation and spot checks
- **Critical Detection**: Identifies important bills automatically
- **Priority Alerts**: Immediate notifications for federal issues

## 🛠 Advanced Usage

### Manual Controls
```bash
# Stop the system
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# Run federal-only scraper
docker-compose exec api python manage.py run --type federal

# Check federal priority status
docker-compose exec api python manage.py federal-check
```

### Environment Configuration
Customize your deployment by editing `.env`:

```bash
# Federal Priority Settings
FEDERAL_PRIORITY_ENABLED=true
FEDERAL_CHECK_INTERVAL=4  # hours
FEDERAL_AI_SUMMARIES=true

# API Security
API_RATE_LIMIT=1000
API_KEY_REQUIRED=false

# Data Quality
QUALITY_CHECKS_ENABLED=true
QUALITY_ALERT_THRESHOLD=90
```

## 🔐 Production Deployment

For production use:

1. **Secure Configuration**:
   ```bash
   # Generate secure passwords
   openssl rand -hex 32
   
   # Update .env with production values
   DB_PASSWORD=your_secure_password
   JWT_SECRET_KEY=your_secure_jwt_key
   ```

2. **Enable Security Features**:
   ```bash
   API_KEY_REQUIRED=true
   API_RATE_LIMIT_ENABLED=true
   ```

3. **Configure Backups**:
   ```bash
   BACKUP_ENABLED=true
   BACKUP_SCHEDULE="0 2 * * *"
   ```

## 📊 Federal Bills Priority System

The system includes **comprehensive federal bills monitoring**:

### ✅ Automated Checks
- **Format Validation**: Ensures C-# and S-# identifier formats
- **Title Quality**: Validates title completeness and length
- **Status Progression**: Monitors logical legislative flow
- **Data Freshness**: Alerts on stale federal data
- **Critical Detection**: Identifies high-priority legislation

### 🎯 Priority Features
- **Enhanced Frequency**: Federal bills updated every 4 hours
- **Quality Validation**: Comprehensive spot checks
- **Smart Alerts**: Immediate notification of issues
- **Detailed Reporting**: Federal-specific monitoring reports
- **Critical Bill Tracking**: Special attention to important legislation

### 📋 Federal Monitoring Report
Access detailed federal monitoring via the dashboard or API:
- Check results with pass/warning/fail status
- Actionable recommendations
- Data quality metrics
- Priority bill identification

## 🌍 Data Sources

### Federal (Priority Enhanced)
- **Parliament of Canada**: https://www.ourcommons.ca/
  - Enhanced monitoring with quality checks
  - Priority scheduling and validation
  - AI-powered summaries (optional)

### Provincial/Territorial (14 jurisdictions)
- Complete coverage of all provinces and territories
- Automated daily updates
- Standardized data collection

### Municipal (108 jurisdictions)
- Major cities across all provinces
- Comprehensive local government data
- Scalable collection system

## 🏆 What Makes This Special

### 🚀 **One-Command Setup**
No complex configuration - just run `./setup.sh` and everything works

### 🎨 **Beautiful Interface**
Modern, responsive dashboard that's actually enjoyable to use

### 🇨🇦 **Federal Priority**
Special attention to Canadian federal legislation with enhanced monitoring

### 🔄 **Self-Healing**
Automatic error recovery and retry mechanisms

### 📊 **Data Quality**
Built-in validation and quality assurance systems

### 🛠 **Production Ready**
Enterprise features like rate limiting, authentication, and monitoring

## 🤝 Contributing

This is a complete, production-ready system, but contributions are welcome:

1. **Report Issues**: Use GitHub issues for bugs or suggestions
2. **Add Jurisdictions**: Help expand coverage to more municipalities
3. **Enhance Features**: Contribute to federal monitoring or dashboard features
4. **Documentation**: Improve setup guides and API documentation

## 📄 License

MIT License - Making Canadian civic data accessible to everyone.

## 🙏 Acknowledgments

- **OpenCivicData**: Standards and framework foundation
- **Government of Canada**: Public data availability
- **Canadian Provinces & Municipalities**: Open data initiatives
- **Community**: Feedback and contributions

---

**🇨🇦 OpenPolicy Backend Ash Aug 2025** - The most comprehensive Canadian civic data platform with federal bills priority monitoring and a beautiful modern interface.

**Ready in one command: `./setup.sh`** ✨
