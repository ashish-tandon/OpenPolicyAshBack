# OpenPolicy Merge - Production Deployment Guide

**Version**: 1.0.0  
**Status**: Ready for Production  
**Date**: December 2024  

## 🎯 **Production Deployment Roadmap**

This guide outlines the step-by-step process to deploy OpenPolicy Merge to production and begin serving Canadian civic data.

---

## **Phase 1: Infrastructure Setup (Week 1)**

### **1.1 Server Requirements**

**Minimum Production Specs:**
- **CPU**: 4 vCPUs (8 recommended)
- **RAM**: 8GB (16GB recommended)
- **Storage**: 100GB SSD (500GB recommended)
- **Network**: 1Gbps connection
- **OS**: Ubuntu 22.04 LTS or similar

**Cloud Provider Options:**
- **AWS**: EC2 t3.xlarge with RDS PostgreSQL
- **Google Cloud**: Compute Engine n2-standard-4
- **Azure**: Standard_D4s_v3
- **DigitalOcean**: CPU-Optimized droplet (4 vCPU, 8GB)

### **1.2 Domain & SSL Setup**

```bash
# 1. Purchase domain (recommended: openpolicymerge.ca)
# 2. Configure DNS records
# 3. Set up SSL certificate (Let's Encrypt or CloudFlare)

# Example DNS configuration:
# A record: openpolicymerge.ca -> [SERVER_IP]
# A record: api.openpolicymerge.ca -> [SERVER_IP]
# CNAME: www.openpolicymerge.ca -> openpolicymerge.ca
```

### **1.3 Server Preparation**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install additional tools
sudo apt install -y git htop curl jq nginx certbot python3-certbot-nginx

# Configure firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### **1.4 Environment Configuration**

```bash
# Clone the repository
git clone https://github.com/your-org/OpenPolicyMerge.git
cd OpenPolicyMerge

# Create production environment file
cp .env.example .env

# Edit production configuration
nano .env
```

**Production `.env` Configuration:**
```bash
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info
SECRET_KEY=[GENERATE_SECURE_KEY]

# Domain Configuration  
DOMAIN=openpolicymerge.ca
API_DOMAIN=api.openpolicymerge.ca
CORS_ORIGINS=https://openpolicymerge.ca,https://www.openpolicymerge.ca

# Database (use managed service in production)
DATABASE_URL=postgresql://user:password@db-host:5432/openpolicy_merge
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100

# Redis (use managed service in production)
REDIS_URL=redis://redis-host:6379/0

# Security
ALLOWED_HOSTS=openpolicymerge.ca,www.openpolicymerge.ca,api.openpolicymerge.ca

# Monitoring
SENTRY_DSN=[YOUR_SENTRY_DSN]
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true

# Scraping
SCRAPING_ENABLED=true
SCRAPING_SCHEDULE=0 2 * * *  # Daily at 2 AM UTC

# External APIs
REPRESENT_API_URL=https://represent.opennorth.ca
PARLIAMENT_API_URL=https://www.ourcommons.ca
```

---

## **Phase 2: Production Deployment (Week 1-2)**

### **2.1 Initial Deployment**

```bash
# Deploy with monitoring
./deploy.sh --monitoring

# Verify deployment
./monitor.sh

# Check health
curl https://openpolicymerge.ca/health
```

### **2.2 SSL & Reverse Proxy Setup**

```bash
# Install SSL certificate
sudo certbot --nginx -d openpolicymerge.ca -d www.openpolicymerge.ca -d api.openpolicymerge.ca

# Configure Nginx for production
sudo nano /etc/nginx/sites-available/openpolicy-merge
```

**Production Nginx Configuration:**
```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name openpolicymerge.ca www.openpolicymerge.ca;
    return 301 https://$server_name$request_uri;
}

# Main application
server {
    listen 443 ssl http2;
    server_name openpolicymerge.ca www.openpolicymerge.ca;
    
    ssl_certificate /etc/letsencrypt/live/openpolicymerge.ca/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/openpolicymerge.ca/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy to application
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# API subdomain
server {
    listen 443 ssl http2;
    server_name api.openpolicymerge.ca;
    
    ssl_certificate /etc/letsencrypt/live/openpolicymerge.ca/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/openpolicymerge.ca/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **2.3 Database Migration & Initial Data Load**

```bash
# Run database initialization
docker-compose exec openpolicy-merge python -c "
from src.database.config import initialize_database
initialize_database()
"

# Load initial jurisdictions data
docker-compose exec openpolicy-merge python -c "
from src.database.config import get_db
from src.database.models import Jurisdiction, JurisdictionType

# Add sample jurisdictions
jurisdictions = [
    {'name': 'Canada', 'type': JurisdictionType.FEDERAL, 'code': 'CA'},
    {'name': 'Ontario', 'type': JurisdictionType.PROVINCIAL, 'code': 'ON'},
    {'name': 'Quebec', 'type': JurisdictionType.PROVINCIAL, 'code': 'QC'},
    {'name': 'Toronto', 'type': JurisdictionType.MUNICIPAL, 'code': 'toronto'},
    {'name': 'Montreal', 'type': JurisdictionType.MUNICIPAL, 'code': 'montreal'},
]

with next(get_db()) as db:
    for j_data in jurisdictions:
        jurisdiction = Jurisdiction(**j_data)
        db.add(jurisdiction)
    db.commit()
"

# Start initial data scraping
docker-compose exec openpolicy-merge python -c "
from src.scrapers.manager import scraper_manager, ScraperType
import asyncio

async def initial_scrape():
    # Start with Represent API data
    result = await scraper_manager.run_scraper(
        ScraperType.REPRESENT_API,
        'federal_canada'
    )
    print(f'Represent API scrape: {result}')

asyncio.run(initial_scrape())
"
```

---

## **Phase 3: Monitoring & Optimization (Week 2-3)**

### **3.1 Production Monitoring Setup**

```bash
# Start monitoring stack
docker-compose --profile monitoring up -d

# Configure Grafana dashboards
# Access: https://openpolicymerge.ca:3001
# Default: admin/admin (change immediately)
```

### **3.2 Performance Optimization**

```bash
# Database optimization
docker-compose exec db psql -U openpolicy -d openpolicy_merge -c "
-- Analyze database statistics
ANALYZE;

-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"

# Application performance monitoring
curl https://api.openpolicymerge.ca/metrics | grep -E '(request_duration|request_count)'
```

### **3.3 Backup & Recovery Setup**

```bash
# Set up automated backups
crontab -e

# Add backup schedule (daily at 3 AM)
0 3 * * * /path/to/OpenPolicyMerge/backup.sh >> /var/log/openpolicy-backup.log 2>&1

# Test backup and restore
./backup.sh
# Verify backup files in ./backups/
```

---

## **Phase 4: Data Population & Validation (Week 3-4)**

### **4.1 Comprehensive Data Collection**

```bash
# Run comprehensive scraping for all data sources
docker-compose exec openpolicy-merge python -c "
from src.scrapers.manager import scraper_manager
import asyncio

async def full_data_collection():
    print('Starting comprehensive data collection...')
    
    # Run all available scrapers
    results = await scraper_manager.run_comprehensive_scrape()
    
    for scraper_id, result in results.items():
        print(f'{scraper_id}: {result.status} - {result.records_new} new records')

asyncio.run(full_data_collection())
"
```

### **4.2 Data Quality Validation**

```bash
# Run data quality checks
docker-compose exec openpolicy-merge python -c "
from src.database.config import get_db
from src.database.models import *

with next(get_db()) as db:
    # Check data counts
    print(f'Jurisdictions: {db.query(Jurisdiction).count()}')
    print(f'Representatives: {db.query(Representative).count()}')
    print(f'Bills: {db.query(Bill).count()}')
    
    # Check data quality issues
    issues = db.query(DataQualityIssue).filter(
        DataQualityIssue.resolved == False
    ).count()
    print(f'Open data quality issues: {issues}')
"
```

### **4.3 API Validation**

```bash
# Test key API endpoints
echo "Testing API endpoints..."

# Health check
curl -f https://api.openpolicymerge.ca/health

# Jurisdictions
curl -f https://api.openpolicymerge.ca/api/v1/jurisdictions?limit=5

# Representatives
curl -f https://api.openpolicymerge.ca/api/v1/representatives?limit=5

# Bills
curl -f https://api.openpolicymerge.ca/api/v1/bills?limit=5

# Search
curl -f "https://api.openpolicymerge.ca/api/v1/search?q=toronto"

echo "✅ API validation complete"
```

---

## **Phase 5: Launch & Go-Live (Week 4)**

### **5.1 Pre-Launch Checklist**

- [ ] **Infrastructure**: Server, domain, SSL certificates configured
- [ ] **Application**: Deployed and running successfully
- [ ] **Database**: Populated with initial data from all sources
- [ ] **Monitoring**: Grafana dashboards showing healthy metrics
- [ ] **Backups**: Automated backup system tested and working
- [ ] **API Documentation**: Swagger docs accessible and complete
- [ ] **Performance**: Load testing completed with acceptable results
- [ ] **Security**: Security audit completed and vulnerabilities addressed

### **5.2 Launch Communications**

```markdown
# Launch Announcement Template

🎉 **OpenPolicy Merge is Now Live!**

We're excited to announce the launch of OpenPolicy Merge - Canada's first unified civic data platform!

## What's Available:
- **200+ Jurisdictions**: Federal, provincial, and municipal data
- **Real-time Updates**: Daily data collection and validation
- **Modern APIs**: REST and GraphQL with comprehensive documentation
- **Open Source**: Fully transparent and community-driven

## Access Points:
- **Main Platform**: https://openpolicymerge.ca
- **API Access**: https://api.openpolicymerge.ca
- **Documentation**: https://openpolicymerge.ca/docs
- **Source Code**: https://github.com/your-org/OpenPolicyMerge

## For Developers:
- Complete REST API with Swagger documentation
- GraphQL endpoint for complex queries
- Real-time WebSocket connections
- Comprehensive data coverage across all government levels

## Get Started:
Visit https://openpolicymerge.ca to explore Canadian civic data like never before!
```

### **5.3 Post-Launch Monitoring**

```bash
# Monitor launch metrics
./monitor.sh

# Watch for errors
docker-compose logs -f --tail=100

# Check performance
curl -s https://api.openpolicymerge.ca/metrics | grep request_duration

# Monitor user activity
tail -f /var/log/nginx/access.log
```

---

## **Phase 6: Post-Launch Operations (Ongoing)**

### **6.1 Daily Operations**

```bash
# Daily health check script
#!/bin/bash
echo "$(date): Daily OpenPolicy Merge Health Check"

# Check application health
curl -f https://openpolicymerge.ca/health || echo "❌ Health check failed"

# Check API response times
response_time=$(curl -o /dev/null -s -w '%{time_total}' https://api.openpolicymerge.ca/api/v1/jurisdictions)
echo "API response time: ${response_time}s"

# Check database connections
docker-compose exec db psql -U openpolicy -d openpolicy_merge -c "SELECT COUNT(*) FROM pg_stat_activity;" || echo "❌ Database check failed"

# Check scraper status
docker-compose exec openpolicy-merge python -c "
from src.scrapers.manager import scraper_manager
stats = scraper_manager.get_scraper_stats()
print(f'Scraper stats: {stats}')
"
```

### **6.2 Weekly Maintenance**

```bash
# Weekly maintenance script
#!/bin/bash
echo "$(date): Weekly OpenPolicy Merge Maintenance"

# Update system packages
sudo apt update && sudo apt upgrade -y

# Clean up Docker images
docker system prune -f

# Backup database
./backup.sh

# Check disk usage
df -h

# Update SSL certificates
sudo certbot renew --nginx

# Restart services if needed
docker-compose restart openpolicy-merge
```

### **6.3 Performance Monitoring**

Set up alerts for:
- **Response Time**: > 500ms average
- **Error Rate**: > 1% of requests
- **Database Connections**: > 80% of pool
- **Disk Usage**: > 85% full
- **Memory Usage**: > 90% utilized
- **Failed Scrapes**: > 3 consecutive failures

---

## **📊 Success Metrics**

### **Technical KPIs**
- **Uptime**: > 99.9%
- **API Response Time**: < 200ms average
- **Data Freshness**: < 24 hours for all sources
- **Error Rate**: < 0.1%
- **Test Coverage**: > 90%

### **Business KPIs**
- **API Requests**: Track daily/monthly usage
- **Data Coverage**: Number of jurisdictions and representatives
- **User Engagement**: Frontend page views and interactions
- **Developer Adoption**: API key registrations and usage

### **Data Quality KPIs**
- **Cross-validation Rate**: > 95% data agreement between sources
- **Scraping Success Rate**: > 98% successful scrapes
- **Data Completeness**: > 90% fields populated for active records
- **Update Frequency**: Daily updates for all active jurisdictions

---

## **🆘 Troubleshooting Guide**

### **Common Issues**

**Application won't start:**
```bash
# Check logs
docker-compose logs openpolicy-merge

# Check database connection
docker-compose exec db pg_isready -U openpolicy

# Restart services
docker-compose restart
```

**High response times:**
```bash
# Check database performance
docker-compose exec db psql -U openpolicy -d openpolicy_merge -c "
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;
"

# Check system resources
htop
df -h
```

**Scraping failures:**
```bash
# Check scraper logs
docker-compose logs celery-worker

# Manual scraper test
docker-compose exec openpolicy-merge python -c "
from src.scrapers.manager import scraper_manager, ScraperType
import asyncio
result = asyncio.run(scraper_manager.run_scraper(ScraperType.REPRESENT_API, 'test'))
print(result)
"
```

---

## **📞 Support & Maintenance**

### **Emergency Contacts**
- **Technical Issues**: [Your technical team contacts]
- **Infrastructure**: [Your DevOps team contacts]
- **Data Quality**: [Your data team contacts]

### **Escalation Process**
1. **Level 1**: Check monitoring dashboards and logs
2. **Level 2**: Run diagnostic scripts and health checks
3. **Level 3**: Contact technical team for investigation
4. **Level 4**: Emergency rollback if needed

### **Maintenance Windows**
- **Preferred**: Sundays 2:00-4:00 AM Eastern Time
- **Emergency**: Any time with advance notice
- **Updates**: Weekly minor updates, monthly major updates

---

**🎯 This deployment guide ensures a smooth transition from development to production, with comprehensive monitoring, maintenance procedures, and success metrics to track the platform's performance and impact.**