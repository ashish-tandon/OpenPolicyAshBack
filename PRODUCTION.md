# Production Deployment Guide

## 🚀 Quick Production Setup

### 1. Server Requirements
- **OS**: Ubuntu 20.04+ or CentOS 8+
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 50GB minimum, 100GB recommended
- **CPU**: 2 cores minimum, 4 cores recommended
- **Network**: Outbound internet access for scraping

### 2. Install Dependencies
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login to apply docker group changes
```

### 3. Deploy Application
```bash
# Clone repository
git clone <your-repo-url>
cd openpolicy-database

# Run production setup
./setup.sh
```

## 🔐 Security Configuration

### 1. Environment Security
```bash
# Generate secure passwords
DB_PASSWORD=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
API_KEY=$(openssl rand -hex 32)

# Update .env file
cat > .env << EOF
# Production Configuration
ENVIRONMENT=production
DEBUG=false

# Database Security
DB_PASSWORD=$DB_PASSWORD

# API Security
JWT_SECRET_KEY=$JWT_SECRET_KEY
API_KEY_REQUIRED=true
API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT=1000

# Monitoring
FLOWER_BASIC_AUTH=admin:$(openssl rand -hex 16)
EOF
```

### 2. Firewall Configuration
```bash
# Configure firewall (Ubuntu)
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 3000/tcp    # Dashboard
sudo ufw allow 8000/tcp    # API
sudo ufw allow 5555/tcp    # Flower (optional, for monitoring)
sudo ufw enable

# For production, consider restricting dashboard and flower to specific IPs
sudo ufw delete allow 3000/tcp
sudo ufw delete allow 5555/tcp
sudo ufw allow from YOUR_ADMIN_IP to any port 3000
sudo ufw allow from YOUR_ADMIN_IP to any port 5555
```

## 🌐 Reverse Proxy Setup (Nginx)

### 1. Install Nginx
```bash
sudo apt update
sudo apt install nginx
```

### 2. Configure Nginx
```bash
sudo cat > /etc/nginx/sites-available/openpolicy << 'EOF'
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration (replace with your certificates)
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # Dashboard
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Flower monitoring (restrict access)
    location /monitoring/ {
        # Basic auth for additional security
        auth_basic "Monitoring";
        auth_basic_user_file /etc/nginx/.htpasswd;
        
        proxy_pass http://localhost:5555/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/openpolicy /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔒 SSL Certificate Setup

### Option 1: Let's Encrypt (Free)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Option 2: Custom Certificate
```bash
# Place your certificates
sudo mkdir -p /etc/ssl/openpolicy
sudo cp your-certificate.crt /etc/ssl/openpolicy/
sudo cp your-private.key /etc/ssl/openpolicy/
sudo chmod 600 /etc/ssl/openpolicy/your-private.key

# Update nginx configuration paths
```

## 📊 Monitoring Setup

### 1. Log Management
```bash
# Create log directory
sudo mkdir -p /var/log/openpolicy
sudo chown -R $USER:$USER /var/log/openpolicy

# Configure log rotation
sudo cat > /etc/logrotate.d/openpolicy << 'EOF'
/var/log/openpolicy/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF
```

### 2. System Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop netstat-nat

# Setup system monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== OpenPolicy System Status ===" 
docker-compose ps
echo ""
echo "=== System Resources ==="
free -h
df -h
echo ""
echo "=== Network Connections ==="
netstat -tlnp | grep -E "(3000|8000|5555|5432|6379)"
EOF

chmod +x monitor.sh
```

## 💾 Backup Strategy

### 1. Database Backup
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/openpolicy"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
docker-compose exec -T postgres pg_dump -U openpolicy opencivicdata > $BACKUP_DIR/database_$DATE.sql

# Compress and clean old backups
gzip $BACKUP_DIR/database_$DATE.sql
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/database_$DATE.sql.gz"
EOF

chmod +x backup.sh

# Schedule daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/backup.sh") | crontab -
```

### 2. System Backup
```bash
# Create system state backup
cat > system_backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/openpolicy"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz .env docker-compose.yml

# Backup custom configurations
cp -r dashboard/src/config $BACKUP_DIR/dashboard_config_$DATE/ 2>/dev/null || true

echo "System backup completed: $BACKUP_DIR/"
EOF

chmod +x system_backup.sh
```

## 🔄 Auto-Updates

### 1. System Updates
```bash
# Create update script
cat > update_system.sh << 'EOF'
#!/bin/bash
echo "Updating OpenPolicy Database..."

# Pull latest changes
git pull

# Rebuild and restart services
docker-compose build
docker-compose up -d

# Run health check
sleep 30
python3 test_system.py

echo "Update completed!"
EOF

chmod +x update_system.sh
```

### 2. Automated Maintenance
```bash
# Create maintenance script
cat > maintenance.sh << 'EOF'
#!/bin/bash

# Clean old Docker images
docker image prune -f

# Clean old logs
find /var/log/openpolicy -name "*.log" -mtime +7 -delete

# Restart services if needed
if [ "$(docker-compose ps -q)" ]; then
    docker-compose restart
fi

echo "Maintenance completed"
EOF

chmod +x maintenance.sh

# Schedule weekly maintenance
(crontab -l 2>/dev/null; echo "0 1 * * 0 /path/to/maintenance.sh") | crontab -
```

## ⚡ Performance Optimization

### 1. Database Optimization
```bash
# Add to docker-compose.yml postgres service environment:
POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements
POSTGRES_MAX_CONNECTIONS=200
POSTGRES_SHARED_BUFFERS=256MB
POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
```

### 2. Application Optimization
```bash
# Update .env for production
API_WORKERS=4
CELERY_CONCURRENCY=4
REDIS_MAXMEMORY=512mb
REDIS_MAXMEMORY_POLICY=allkeys-lru
```

## 📈 Scaling Options

### 1. Horizontal Scaling
```bash
# Scale specific services
docker-compose up -d --scale celery_worker=3
docker-compose up -d --scale api=2
```

### 2. Database Scaling
```bash
# Add read replicas
# Add to docker-compose.yml:
postgres_read:
  image: postgres:17
  environment:
    POSTGRES_MASTER_SERVICE: postgres
    # Configure as read replica
```

## 🚨 Alerting Setup

### 1. Health Check Monitoring
```bash
# Create health monitor
cat > health_monitor.sh << 'EOF'
#!/bin/bash
WEBHOOK_URL="your-slack-or-webhook-url"

if ! curl -f http://localhost:8000/health >/dev/null 2>&1; then
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"🚨 OpenPolicy Database API is down!"}' \
        $WEBHOOK_URL
fi

if ! curl -f http://localhost:3000 >/dev/null 2>&1; then
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"🚨 OpenPolicy Database Dashboard is down!"}' \
        $WEBHOOK_URL
fi
EOF

chmod +x health_monitor.sh

# Check every 5 minutes
(crontab -l 2>/dev/null; echo "*/5 * * * * /path/to/health_monitor.sh") | crontab -
```

## 📋 Production Checklist

### Pre-Deployment
- [ ] Server meets minimum requirements
- [ ] Domain name configured
- [ ] SSL certificates ready
- [ ] Firewall rules configured
- [ ] Backup strategy planned

### Security
- [ ] Strong passwords generated
- [ ] Environment variables secured
- [ ] API authentication enabled
- [ ] Rate limiting configured
- [ ] Monitoring access restricted

### Deployment
- [ ] Application deployed successfully
- [ ] All services running
- [ ] Health checks passing
- [ ] SSL working correctly
- [ ] Monitoring accessible

### Post-Deployment
- [ ] Backups configured and tested
- [ ] Alerting system working
- [ ] Documentation updated
- [ ] Team access configured
- [ ] Monitoring dashboard setup

---

**🇨🇦 OpenPolicy Database** is now production-ready with enterprise-grade security, monitoring, and reliability features.

**Ready to serve Canadian civic data at scale!** 🚀