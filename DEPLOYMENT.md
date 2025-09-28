# iwhereGIS Grid Engine - Deployment Guide

## Table of Contents
- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ / CentOS 8+ / macOS 11+
- **Python**: 3.8 or higher
- **Memory**: Minimum 2GB RAM (4GB recommended)
- **Storage**: Minimum 10GB free space
- **CPU**: 2+ cores recommended

### Software Dependencies
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv
sudo apt-get install -y gdal-bin libgdal-dev
sudo apt-get install -y redis-server nginx
sudo apt-get install -y docker.io docker-compose

# CentOS/RHEL
sudo yum install -y python3 python3-pip
sudo yum install -y gdal gdal-devel
sudo yum install -y redis nginx
sudo yum install -y docker docker-compose
```

## Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/iwheregis-grid-engine.git
cd iwheregis-grid-engine
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env file with your settings
nano .env
```

### 5. Run Development Server
```bash
# Using Python directly
python app.py

# Using Make
make run-dev

# With auto-reload
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```

## Production Deployment

### 1. System Preparation

```bash
# Create application user
sudo useradd -m -s /bin/bash iwheregis
sudo usermod -aG sudo iwheregis

# Create directories
sudo mkdir -p /opt/iwheregis
sudo mkdir -p /var/log/iwheregis
sudo mkdir -p /var/lib/iwheregis/data
sudo chown -R iwheregis:iwheregis /opt/iwheregis /var/log/iwheregis /var/lib/iwheregis
```

### 2. Application Deployment

```bash
# Switch to application user
sudo su - iwheregis

# Clone and setup
cd /opt/iwheregis
git clone https://github.com/yourusername/iwheregis-grid-engine.git .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure production environment
cp .env.example .env
# Edit with production settings
vim .env
```

### 3. Gunicorn Setup

Create systemd service file `/etc/systemd/system/iwheregis.service`:

```ini
[Unit]
Description=iwhereGIS Grid Engine
After=network.target redis.service
Requires=redis.service

[Service]
Type=notify
User=iwheregis
Group=iwheregis
WorkingDirectory=/opt/iwheregis
Environment="PATH=/opt/iwheregis/venv/bin"
ExecStart=/opt/iwheregis/venv/bin/gunicorn \
    --bind 127.0.0.1:5000 \
    --workers 4 \
    --worker-class sync \
    --timeout 30 \
    --access-logfile /var/log/iwheregis/access.log \
    --error-logfile /var/log/iwheregis/error.log \
    --log-level info \
    app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
KillSignal=SIGTERM
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable iwheregis
sudo systemctl start iwheregis
sudo systemctl status iwheregis
```

### 4. Nginx Configuration

Create nginx configuration `/etc/nginx/sites-available/iwheregis`:

```nginx
upstream iwheregis_backend {
    server 127.0.0.1:5000 fail_timeout=0;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Logging
    access_log /var/log/nginx/iwheregis_access.log;
    error_log /var/log/nginx/iwheregis_error.log;
    
    # Static files
    location /static {
        alias /opt/iwheregis/static;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
    
    # API endpoints
    location / {
        proxy_pass http://iwheregis_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
        proxy_connect_timeout 10s;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/iwheregis /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. SSL Certificate (Let's Encrypt)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Docker Deployment

### 1. Quick Start

```bash
# Build and run with docker-compose
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f

# Stop
docker-compose down
```

### 2. Production Docker Deployment

```bash
# Build production image
docker build -t iwheregis/grid-engine:latest .

# Run with environment file
docker run -d \
    --name iwheregis-app \
    --env-file .env \
    -p 5000:5000 \
    -v $(pwd)/data:/app/data:ro \
    -v $(pwd)/logs:/app/logs \
    --restart unless-stopped \
    iwheregis/grid-engine:latest
```

### 3. Docker Swarm Deployment

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml iwheregis

# Scale service
docker service scale iwheregis_app=3

# Update service
docker service update --image iwheregis/grid-engine:v2.0.0 iwheregis_app
```

## Cloud Deployment

### AWS EC2

```bash
# 1. Launch EC2 instance (Ubuntu 20.04, t3.medium or larger)

# 2. SSH to instance
ssh -i your-key.pem ubuntu@ec2-instance-ip

# 3. Install dependencies
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# 4. Deploy application
git clone https://github.com/yourusername/iwheregis-grid-engine.git
cd iwheregis-grid-engine
docker-compose up -d
```

### Google Cloud Platform

```bash
# 1. Create GCE instance
gcloud compute instances create iwheregis-app \
    --machine-type=n1-standard-2 \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB

# 2. SSH to instance
gcloud compute ssh iwheregis-app

# 3. Deploy using Docker
# Follow Docker deployment steps above
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iwheregis-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: iwheregis
  template:
    metadata:
      labels:
        app: iwheregis
    spec:
      containers:
      - name: app
        image: iwheregis/grid-engine:latest
        ports:
        - containerPort: 5000
        env:
        - name: APP_ENV
          value: "production"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
---
apiVersion: v1
kind: Service
metadata:
  name: iwheregis-service
spec:
  selector:
    app: iwheregis
  ports:
  - port: 80
    targetPort: 5000
  type: LoadBalancer
```

Deploy to Kubernetes:
```bash
kubectl apply -f k8s-deployment.yaml
kubectl get pods
kubectl get services
```

## Configuration

### Environment Variables

Key environment variables for production:

```bash
# Application
APP_ENV=production
APP_NAME="iwhereGIS Grid Engine"
DEBUG=False

# Server
HOST=0.0.0.0
PORT=5000
WORKERS=4

# Security
API_KEY_REQUIRED=True
API_SECRET_KEY=your-secure-api-key
JWT_SECRET_KEY=your-secure-jwt-key
CORS_ENABLED=True
CORS_ORIGINS=https://your-domain.com

# Database (if using)
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/iwheregis/app.log

# Performance
CACHE_ENABLED=True
CACHE_TTL=300
MAX_GRID_GENERATION=10000
```

### Performance Tuning

```bash
# Nginx optimization
worker_processes auto;
worker_connections 2048;

# Gunicorn optimization
--workers 4  # 2 * CPU cores + 1
--worker-connections 1000
--max-requests 1000
--max-requests-jitter 50

# Redis optimization
maxmemory 256mb
maxmemory-policy allkeys-lru
```

## Monitoring

### 1. Application Metrics

```bash
# Check application health
curl https://your-domain.com/api/v1/health

# Get statistics
curl https://your-domain.com/api/v1/status
```

### 2. Log Monitoring

```bash
# Application logs
tail -f /var/log/iwheregis/app.log

# Nginx logs
tail -f /var/log/nginx/iwheregis_access.log

# Docker logs
docker-compose logs -f app
```

### 3. System Monitoring

```bash
# Install monitoring tools
sudo apt-get install -y htop iotop nethogs

# Monitor resources
htop  # CPU and memory
iotop  # Disk I/O
nethogs  # Network usage
```

### 4. Prometheus Integration

Add to `docker-compose.yml`:
```yaml
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Find process using port
sudo lsof -i :5000
# Kill process
sudo kill -9 <PID>
```

#### 2. Permission Denied
```bash
# Fix permissions
sudo chown -R iwheregis:iwheregis /opt/iwheregis
sudo chmod -R 755 /opt/iwheregis
```

#### 3. Redis Connection Failed
```bash
# Check Redis status
sudo systemctl status redis
# Restart Redis
sudo systemctl restart redis
```

#### 4. High Memory Usage
```bash
# Check memory usage
free -h
# Clear cache
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=True

# Run with verbose output
gunicorn --log-level debug app:app
```

### Health Checks

```bash
# Create health check script
cat > /opt/iwheregis/health_check.sh << 'EOF'
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/v1/health)
if [ $response -eq 200 ]; then
    echo "Health check passed"
    exit 0
else
    echo "Health check failed with status: $response"
    exit 1
fi
EOF

chmod +x /opt/iwheregis/health_check.sh
```

## Backup and Recovery

### Backup Strategy

```bash
# Backup script
cat > /opt/iwheregis/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/iwheregis"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup data
tar -czf $BACKUP_DIR/data_$DATE.tar.gz /var/lib/iwheregis/data
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /opt/iwheregis/.env

# Backup database (if using)
# pg_dump -U user dbname > $BACKUP_DIR/db_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/iwheregis/backup.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /opt/iwheregis/backup.sh
```

### Recovery Process

```bash
# Restore from backup
tar -xzf /var/backups/iwheregis/data_20240101_020000.tar.gz -C /
tar -xzf /var/backups/iwheregis/config_20240101_020000.tar.gz -C /

# Restart services
sudo systemctl restart iwheregis
```

## Security Best Practices

1. **Use HTTPS**: Always use SSL/TLS in production
2. **API Keys**: Enable API key authentication for production
3. **Rate Limiting**: Configure rate limiting to prevent abuse
4. **Firewall**: Configure firewall rules
5. **Updates**: Keep system and dependencies updated
6. **Monitoring**: Set up monitoring and alerting
7. **Backups**: Regular automated backups
8. **Secrets Management**: Use environment variables or secret management tools

## Support

For issues and questions:
- GitHub Issues: [https://github.com/yourusername/iwheregis-grid-engine/issues](https://github.com/yourusername/iwheregis-grid-engine/issues)
- Documentation: [https://docs.iwheregis.com](https://docs.iwheregis.com)
- Email: support@iwheregis.com