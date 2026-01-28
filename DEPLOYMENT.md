# Deployment Guide

This guide covers deploying the Firewall Discovery Tool to your on-premises infrastructure.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Network access to:
  - Unicorn API
  - Illumio API
  - (Future) Checkpoint APIs
  - (Future) NSX API
- SSL certificates (for HTTPS in production)

## Production Deployment

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

### 2. Application Setup

```bash
# Create application directory
sudo mkdir -p /opt/firewall-discovery-tool
cd /opt/firewall-discovery-tool

# Copy application files (use git, scp, or other method)
# For example:
git clone <your-repo> .
# OR
scp -r firewall-discovery-tool/* user@server:/opt/firewall-discovery-tool/
```

### 3. Configuration

```bash
# Create environment file
cp backend/.env.example backend/.env

# Edit with production values
sudo nano backend/.env
```

**Production `.env` example:**
```env
UNICORN_API_URL=https://unicorn.yourcompany.com/api
UNICORN_API_KEY=prod_api_key_here

ILLUMIO_API_URL=https://illumio.yourcompany.com/api/v2
ILLUMIO_API_KEY=prod_illumio_key_here

LOG_LEVEL=INFO
API_TIMEOUT=30
```

### 4. SSL/TLS Configuration (HTTPS)

For production, configure HTTPS using Let's Encrypt or your organization's certificates.

**Option A: Using Let's Encrypt with Nginx**

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d firewall-tool.yourcompany.com
```

**Option B: Using Organization Certificates**

Update `frontend/nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name firewall-tool.yourcompany.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... rest of configuration
}

server {
    listen 80;
    server_name firewall-tool.yourcompany.com;
    return 301 https://$server_name$request_uri;
}
```

Mount certificates in `docker-compose.yml`:

```yaml
frontend:
  volumes:
    - /path/to/certs:/etc/nginx/ssl:ro
```

### 5. Update Docker Compose for Production

Edit `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: firewall-tool-backend
    restart: always
    environment:
      - UNICORN_API_URL=${UNICORN_API_URL}
      - UNICORN_API_KEY=${UNICORN_API_KEY}
      - ILLUMIO_API_URL=${ILLUMIO_API_URL}
      - ILLUMIO_API_KEY=${ILLUMIO_API_KEY}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    networks:
      - firewall-tool-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: firewall-tool-frontend
    ports:
      - "443:443"
      - "80:80"
    depends_on:
      - backend
    restart: always
    volumes:
      - /etc/ssl/certs:/etc/nginx/ssl:ro  # Mount SSL certificates
    networks:
      - firewall-tool-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

networks:
  firewall-tool-network:
    driver: bridge
```

### 6. Build and Deploy

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f
```

### 7. Verify Deployment

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost

# Test API endpoint
curl -X POST http://localhost:8000/api/v1/discover-firewalls \
  -H "Content-Type: application/json" \
  -d '{"application_name": "TestApp"}'
```

## Monitoring and Maintenance

### Log Management

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service logs
docker-compose logs backend
docker-compose logs frontend

# View last 100 lines
docker-compose logs --tail=100
```

### Updating the Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Verify update
docker-compose ps
docker-compose logs -f
```

### Backup and Recovery

**Backup Configuration:**
```bash
# Backup environment file
sudo cp backend/.env /backup/firewall-tool/.env.$(date +%Y%m%d)

# Backup docker-compose configuration
sudo cp docker-compose.yml /backup/firewall-tool/docker-compose.yml.$(date +%Y%m%d)
```

**Recovery:**
```bash
# Restore configuration
sudo cp /backup/firewall-tool/.env.YYYYMMDD backend/.env

# Rebuild and restart
docker-compose down
docker-compose up -d
```

### Performance Tuning

**Backend Performance:**

Update `docker-compose.yml`:
```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      reservations:
        cpus: '1.0'
        memory: 1G
```

**Frontend Performance:**

Update `frontend/nginx.conf` for caching:
```nginx
location / {
    try_files $uri $uri/ /index.html;
    
    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## High Availability Setup

For production environments requiring high availability:

### Load Balancer Configuration

Use an external load balancer (e.g., HAProxy, Nginx, F5) to distribute traffic across multiple instances:

```
                    ┌─────────────┐
                    │Load Balancer│
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
      ┌─────▼────┐   ┌─────▼────┐   ┌─────▼────┐
      │Instance 1│   │Instance 2│   │Instance 3│
      └──────────┘   └──────────┘   └──────────┘
```

**HAProxy Example Configuration:**
```
frontend http_front
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/firewall-tool.pem
    default_backend http_back

backend http_back
    balance roundrobin
    option httpchk GET /health
    server instance1 10.0.1.10:80 check
    server instance2 10.0.1.11:80 check
    server instance3 10.0.1.12:80 check
```

### Container Orchestration

For larger deployments, consider Kubernetes or Docker Swarm:

**Docker Swarm Example:**
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml firewall-tool

# Scale services
docker service scale firewall-tool_backend=3
docker service scale firewall-tool_frontend=2
```

## Security Hardening

### 1. Network Security

```bash
# Configure firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Container Security

Update `docker-compose.yml`:
```yaml
backend:
  security_opt:
    - no-new-privileges:true
  read_only: true
  tmpfs:
    - /tmp
```

### 3. Secrets Management

For production, use Docker secrets or external secret management:

```bash
# Create secrets
echo "your-api-key" | docker secret create unicorn_api_key -

# Use in docker-compose.yml
services:
  backend:
    secrets:
      - unicorn_api_key
    environment:
      - UNICORN_API_KEY_FILE=/run/secrets/unicorn_api_key

secrets:
  unicorn_api_key:
    external: true
```

## Troubleshooting

### Common Issues

**Issue: Backend can't connect to APIs**
```bash
# Check network connectivity
docker-compose exec backend ping -c 3 unicorn-api.yourcompany.com

# Check DNS resolution
docker-compose exec backend nslookup unicorn-api.yourcompany.com

# Verify API credentials
docker-compose exec backend env | grep API
```

**Issue: Frontend can't reach backend**
```bash
# Check backend is running
docker-compose ps backend

# Test backend endpoint
curl http://localhost:8000/health

# Check nginx configuration
docker-compose exec frontend nginx -t
```

**Issue: High memory usage**
```bash
# Check container stats
docker stats

# View container resource usage
docker-compose exec backend ps aux
```

## Rollback Procedure

```bash
# Stop current version
docker-compose down

# Restore previous version
git checkout <previous-commit>

# Or restore from backup
cp /backup/firewall-tool/.env.YYYYMMDD backend/.env

# Rebuild and start
docker-compose build
docker-compose up -d

# Verify
docker-compose logs -f
```

## Monitoring Setup

### Prometheus Integration

Add monitoring to `docker-compose.yml`:

```yaml
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    ports:
      - "9090:9090"
    networks:
      - firewall-tool-network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - firewall-tool-network

volumes:
  prometheus-data:
  grafana-data:
```

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly:**
   - Review application logs
   - Check disk space
   - Monitor response times

2. **Monthly:**
   - Update Docker images
   - Review and rotate API keys if needed
   - Backup configuration

3. **Quarterly:**
   - Security audit
   - Performance review
   - Capacity planning

### Getting Help

- Review logs: `docker-compose logs`
- Check API documentation: http://localhost:8000/docs
- Contact infrastructure team
