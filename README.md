# OpenPolicy Database

A robust, automated, and self-healing system for collecting, storing, and serving Canadian civic data from all levels of government.

## Overview

The OpenPolicy Database system scrapes civic data from **123 active jurisdictions** across Canada:
- **1 Federal jurisdiction** (Parliament of Canada)
- **14 Provincial/Territorial jurisdictions** 
- **108 Municipal jurisdictions** across all provinces

### Data Collected

- **Representatives**: MPs, MPPs/MLAs, Mayors, Councillors with contact information, party affiliation, districts
- **Bills**: Legislative bills with status tracking, sponsors, reading dates
- **Committees**: Standing and special committees with membership
- **Events**: Meetings, votes, readings, and other legislative events
- **Votes**: Individual representative votes on bills and motions

### Key Features

✅ **Comprehensive Coverage**: Scrapes all available Canadian civic data sources  
✅ **Automated Daily Runs**: Scheduled scraping with error recovery  
✅ **REST API**: Full Swagger-documented API for public access  
✅ **Data Quality Monitoring**: Automated validation and issue detection  
✅ **Self-Healing**: Automatic retry and error correction  
✅ **Containerized**: Full Docker Compose deployment  
✅ **Scalable**: Celery-based distributed task processing  

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Scrapers      │    │    Database      │    │      API        │
│                 │    │                  │    │                 │
│ • 123 Regions   │───▶│ • PostgreSQL     │◀───│ • FastAPI       │
│ • Daily Runs    │    │ • Normalized     │    │ • Swagger Docs  │
│ • Auto Retry    │    │ • Validated      │    │ • Public Access │
│ • Error Logging │    │ • Indexed        │    │ • Rate Limited  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                       │                       │
        │               ┌───────────────┐               │
        └──────────────▶│   Scheduler   │◀──────────────┘
                        │               │
                        │ • Celery      │
                        │ • Redis       │
                        │ • Flower UI   │
                        │ • Monitoring  │
                        └───────────────┘
```

## Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd openpolicy-database
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Deploy with Docker
```bash
# Start all services
docker-compose up -d

# Initialize database
docker-compose exec api python manage.py init

# Run test scrapers
docker-compose exec api python manage.py run --test --max-records 5
```

### 4. Access Services
- **API Documentation**: http://localhost:8000/docs
- **Flower Monitoring**: http://localhost:5555
- **Database**: localhost:5432

## Manual Installation

### Prerequisites
- Python 3.13+
- PostgreSQL 17+
- Redis 7+

### Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate regions report
python region_analyzer.py

# 3. Initialize database
python manage.py init

# 4. Start services
# Terminal 1: API
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Celery Worker
celery worker -A src.scheduler.tasks --loglevel=info

# Terminal 3: Celery Beat
celery beat -A src.scheduler.tasks --loglevel=info

# Terminal 4: Flower
celery flower -A src.scheduler.tasks --port=5555
```

## Usage

### Management Commands

```bash
# Initialize database and load jurisdictions
python manage.py init

# Run all scrapers in test mode
python manage.py run --test --max-records 5

# Run specific jurisdiction types
python manage.py run --type federal
python manage.py run --type provincial
python manage.py run --type municipal

# Schedule background tasks
python manage.py schedule test
python manage.py schedule federal

# Check task status
python manage.py check <task-id>

# View database statistics
python manage.py stats
```

### API Endpoints

#### Core Data Access
```http
GET /representatives              # List representatives
GET /representatives/{id}         # Get specific representative
GET /jurisdictions               # List jurisdictions
GET /bills                       # List bills
GET /committees                  # List committees
GET /events                      # List events
GET /votes                       # List votes
```

#### Filtering Examples
```http
# Federal representatives
GET /representatives?jurisdiction_type=federal

# Ontario provincial representatives
GET /representatives?province=ON&jurisdiction_type=provincial

# Toronto city councillors
GET /representatives?jurisdiction_id={toronto-id}&role=Councillor

# Search by name
GET /representatives?search=trudeau

# Liberal party members
GET /representatives?party=Liberal
```

#### Statistics
```http
GET /stats                       # Database statistics
GET /health                      # System health check
```

## Data Sources

### Federal
- **Parliament of Canada**: https://www.ourcommons.ca/
  - MPs, committees, bills, votes

### Provincial/Territorial (14 jurisdictions)
- **Alberta**: https://www.assembly.ab.ca/
- **British Columbia**: https://www.leg.bc.ca/
- **Manitoba**: https://www.gov.mb.ca/legislature/
- **New Brunswick**: https://www.gnb.ca/legis/
- **Newfoundland and Labrador**: https://www.assembly.nl.ca/
- **Northwest Territories**: https://www.assembly.gov.nt.ca/
- **Nova Scotia**: https://nslegislature.ca/
- **Nunavut**: https://www.assembly.nu.ca/
- **Ontario**: https://www.ola.org/
- **Prince Edward Island**: https://www.assembly.pe.ca/
- **Quebec**: http://www.assnat.qc.ca/
- **Saskatchewan**: https://www.legassembly.sk.ca/
- **Yukon**: https://yukonassembly.ca/

### Municipal (108 jurisdictions)
Major cities across all provinces including:
- **Toronto, Ottawa, Hamilton** (Ontario)
- **Montreal, Quebec City, Laval** (Quebec)
- **Vancouver, Surrey, Burnaby** (British Columbia)
- **Calgary, Edmonton** (Alberta)
- **Winnipeg** (Manitoba)
- **Halifax** (Nova Scotia)
- And 97+ more municipalities

## Database Schema

### Core Tables
- **jurisdictions**: Federal/provincial/municipal governments
- **representatives**: Elected officials with contact info
- **bills**: Legislative bills with status tracking
- **committees**: Standing and special committees
- **events**: Meetings, votes, readings
- **votes**: Individual representative votes

### Monitoring Tables
- **scraping_runs**: Execution logs and statistics
- **data_quality_issues**: Automated issue detection

### Key Features
- **UUID primary keys** for all entities
- **Full audit trails** with created/updated timestamps
- **Referential integrity** with foreign key constraints
- **Optimized indexes** for fast queries
- **JSON support** for flexible metadata storage

## Automation & Scheduling

### Scheduled Tasks
- **Daily scraping**: All jurisdictions at midnight UTC
- **Hourly data quality checks**: Validation and issue detection
- **Weekly cleanup**: Old logs and resolved issues

### Manual Task Management
```bash
# Schedule specific tasks
python manage.py schedule federal     # Federal data only
python manage.py schedule provincial  # Provincial data only
python manage.py schedule municipal   # Municipal data only
python manage.py schedule test        # Test run (5 records max)

# Monitor tasks
python manage.py check <task-id>      # Check status
python manage.py cancel <task-id>     # Cancel running task
```

### Error Recovery

The system includes comprehensive error recovery:

1. **Automatic Retry**: Failed scrapers retry with exponential backoff
2. **Source Change Detection**: Monitors for moved URLs or changed formats
3. **Data Validation**: Checks for missing fields and duplicates
4. **Issue Logging**: All errors logged to database with severity levels
5. **Daily Reports**: Automated quality reports with suggested fixes

## Data Quality

### Automated Validation
- **Required field checks**: Name, role, jurisdiction
- **Duplicate detection**: Same person multiple times
- **Contact validation**: Email format, phone number format
- **Relationship integrity**: Representatives belong to valid jurisdictions

### Quality Metrics
- **Completeness**: Percentage of fields populated
- **Accuracy**: Data validation checks passed
- **Freshness**: Time since last successful scrape
- **Consistency**: Cross-reference validation

### Issue Severity Levels
- **Critical**: System failures, complete data loss
- **High**: Missing required data, duplicates
- **Medium**: Missing contact information
- **Low**: Missing optional fields, formatting issues

## Monitoring

### Flower Dashboard (http://localhost:5555)
- **Active tasks**: Currently running scrapers
- **Task history**: Success/failure rates
- **Worker status**: Health and performance
- **Queue monitoring**: Task backlog

### Database Statistics
```bash
python manage.py stats
```
Shows:
- Jurisdiction counts by type
- Representative counts by province/role
- Data quality metrics
- Recent scraping activity

### Logs
- **Application logs**: `/var/log/openpolicy/`
- **Celery logs**: Task execution details
- **Database logs**: Performance and errors
- **Access logs**: API usage statistics

## Performance

### Scalability
- **Horizontal scaling**: Add more Celery workers
- **Database optimization**: Indexed queries, connection pooling
- **Caching**: Redis for frequent queries
- **Rate limiting**: Respectful scraping intervals

### Typical Performance
- **Scraping speed**: ~1000 representatives/minute
- **API response time**: <100ms for most queries
- **Database size**: ~50MB for full Canadian dataset
- **Memory usage**: ~512MB per worker

## Security

### API Security
- **Rate limiting**: Prevents abuse
- **CORS configuration**: Controlled cross-origin access
- **Input validation**: Prevents injection attacks
- **Health checks**: Monitor system status

### Data Privacy
- **Public data only**: No private/personal information
- **Source attribution**: All data linked to original sources
- **Compliance**: Follows robots.txt and API guidelines

### Infrastructure
- **Container isolation**: Docker security boundaries
- **Network policies**: Internal service communication
- **Environment variables**: Secure configuration management

## Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd openpolicy-database

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest

# Code formatting
black src/
isort src/

# Type checking
mypy src/
```

### Adding New Jurisdictions
1. Add scraper to `scrapers/` directory
2. Update `region_analyzer.py`
3. Add jurisdiction to database
4. Test scraper thoroughly
5. Submit pull request

### Data Source Changes
When a jurisdiction changes their website:
1. Update scraper URL and selectors
2. Test data extraction
3. Verify data quality
4. Update documentation

## Deployment

### Production Checklist
- [ ] Set strong database passwords
- [ ] Configure SSL certificates
- [ ] Set up monitoring and alerting
- [ ] Configure backup procedures
- [ ] Set appropriate rate limits
- [ ] Review security settings

### Environment Variables
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=opencivicdata
DB_USER=openpolicy
DB_PASSWORD=secure_password

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Backup Procedures
```bash
# Database backup
pg_dump opencivicdata > backup_$(date +%Y%m%d).sql

# Restore database
psql opencivicdata < backup_20241225.sql
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions, issues, or contributions:
- **Issues**: GitHub Issues
- **Documentation**: `/docs` directory
- **API Docs**: http://localhost:8000/docs

## Acknowledgments

- **OpenCivicData**: Scraper framework and standards
- **Canadian Governments**: Public data sources
- **Community**: Contributors and feedback

---

**OpenPolicy Database** - Making Canadian civic data accessible to everyone.
