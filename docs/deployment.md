# Production Deployment Guide

This guide covers deploying Tact AI to production using Docker and Docker Compose.

## Architecture Overview

The production deployment consists of the following services:

- **Nginx**: Reverse proxy with SSL termination and rate limiting
- **Backend**: FastAPI application with Gunicorn + Uvicorn workers
- **Frontend**: React SPA served by Nginx
- **PostgreSQL**: Primary database with performance optimizations
- **Redis**: Caching and session storage
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- SSL certificates (for HTTPS)
- Domain name pointing to your server
- OpenAI API key
- 4GB+ RAM recommended
- 2+ CPU cores recommended

## Pre-Deployment Checklist

1. **Domain & DNS**
   - Point your domain to the server IP
   - Configure DNS A record(s)

2. **SSL Certificates**
   - Obtain SSL certificates (Let's Encrypt recommended)
   - Place certificates in `docker/ssl/`:
     - `cert.pem` - SSL certificate
     - `key.pem` - Private key

3. **Environment Configuration**
   - Copy `.env.example` to `.env`
   - Generate a strong `SECRET_KEY`: `openssl rand -hex 32`
   - Set `OPENAI_API_KEY` to your actual API key
   - Configure database credentials
   - Set `ENVIRONMENT=production`
   - Set `DEBUG=False`

4. **Server Preparation**
   - Install Docker and Docker Compose
   - Open necessary ports (80, 443) in firewall
   - Ensure sufficient disk space for logs and data

## Deployment Steps

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd tact-ai
cp .env.example .env
# Edit .env with production values
```

### 2. Create SSL Directory

```bash
mkdir -p docker/ssl
# Copy your SSL certificates to docker/ssl/
chmod 600 docker/ssl/*.pem
```

### 3. Build and Start Services

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start all services in detached mode
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps
```

### 4. Run Database Migrations

```bash
# Execute Alembic migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Optional: Create initial admin user (if you have a seed script)
```

### 5. Verify Deployment

```bash
# Check all services are healthy
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Test backend API
curl https://your-domain.com/api/health

# Test frontend (should load React app)
curl https://your-domain.com/ | grep -i react
```

## Docker Configuration

### Backend (`docker/Dockerfile.backend.prod`)

**Multi-stage build** for optimized image size:
- Builder stage: Installs Python dependencies in user directory
- Production stage: Minimal Python 3.11-slim with only runtime dependencies

**Gunicorn configuration**:
- 4 workers (adjust based on CPU cores)
- Uvicorn worker class for async support
- Timeout: 120 seconds
- Keep-alive: 5 seconds
- Max requests per worker: 1000 (prevents memory leaks)
- Access and error logs to stdout

**Security**:
- Non-root user (tactuser, UID 1000)
- Health check endpoint
- Minimal installed packages

### Frontend (`docker/Dockerfile.frontend`)

**Multi-stage build**:
- Builder stage: Node.js 18-alpine, installs dependencies and builds React app
- Production stage: Nginx alpine, serves static assets

**Optimizations**:
- Multi-stage reduces final image size (~20MB vs ~1GB)
- Nginx configured for static file caching (1 year)
- Gzip compression enabled
- Proper Content-Encoding headers

### Nginx Configuration (`docker/nginx.conf`)

**Key features**:
- HTTP to HTTPS redirect
- SSL/TLS 1.2+ only with secure ciphers
- HSTS header (63072000 seconds)
- Security headers (X-Frame-Options, X-Content-Type-Options, etc.)
- Rate limiting: API (10 req/s), Login (5 req/min)
- Static file caching (1 year for hashed assets)
- WebSocket support for `/ws`
- Health check endpoint (`/health`)
- Metrics endpoint (`/metrics`)

### PostgreSQL Configuration

- Version: 15-alpine (lightweight)
- Persistent volume: `postgres_data`
- Performance optimizations in `docker/init.sql`:
  - Extensions: `uuid-ossp`, `pg_stat_statements`
  - Indexes on frequently queried columns
  - Connection pooling recommended (pgBouncer) for production scale
- Health check with `pg_isready`
- Automatic restart

### Redis Configuration

- Version: 7-alpine
- Persistent volume: `redis_data`
- AOF (Append Only File) enabled
- Memory limit: 256MB with LRU eviction
- Health check with `redis-cli ping`
- Automatic restart

## Monitoring

### Prometheus

- Scrapes metrics from backend `/metrics` endpoint
- Configured to also collect PostgreSQL and Redis metrics (requires exporters)
- Data persisted in `prometheus_data` volume
- Accessible at: `http://your-domain.com:9090`

### Grafana

- Pre-configured datasource pointing to Prometheus
- Dashboards auto-provisioned from `docker/grafana/dashboards/`
- Accessible at: `http://your-domain.com:3001`
- Default admin password set via `GRAFANA_PASSWORD` env var

### Exposing Additional Metrics

To collect PostgreSQL and Redis metrics, add the respective exporters to `docker-compose.prod.yml`:

```yaml
postgres-exporter:
  image: quay.io/prometheuscommunity/postgres-exporter:latest
  environment:
    DATA_SOURCE_NAME: "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}?sslmode=disable"
  networks:
    - tact-ai-network
```

## Scaling & Performance Tuning

### Horizontal Scaling

Scale backend workers by modifying `docker-compose.prod.yml`:

```yaml
backend:
  # ... existing config
  deploy:
    replicas: 3
    resources:
      limits:
        cpus: '1'
        memory: 1G
```

Then use Docker Swarm or Kubernetes for orchestration. For simple Docker Compose, manually scale:

```bash
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

### Gunicorn Worker Tuning

Adjust worker count based on CPU cores:
- CPU-bound: 2-4 workers per core
- I/O-bound (this app): 2-4 workers per core is safe

Formula: `workers = (2 * CPU cores) + 1`

Edit `docker/Dockerfile.backend.prod` CMD and rebuild.

### Database Indexing

Add indexes based on query patterns. See `docker/init.sql` for examples.

### Redis Tuning

Adjust memory settings in `docker-compose.prod.yml`:
- `--maxmemory`: Based on dataset size (256MB default)
- `--maxmemory-policy`: Consider `volatile-lru` if you use TTLs

## Backup & Restore

### PostgreSQL Backup

```bash
# Manual backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U tactuser tactai > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U tactuser -d tactai < backup_file.sql
```

### Automated Backups with Cron

On the host, add to crontab:

```bash
0 2 * * * cd /path/to/tact-ai && ./scripts/backup.sh
```

Create `scripts/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/tact-ai"
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U ${POSTGRES_USER:-tactuser} ${POSTGRES_DB:-tactai} | gzip > ${BACKUP_DIR}/tactai_${DATE}.sql.gz
# Keep only last 7 days
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +7 -delete
```

### Redis Persistence

Redis AOF is enabled and persisted in `redis_data` volume. To backup:

```bash
docker-compose -f docker-compose.prod.yml exec redis redis-cli BGSAVE
# Copy RDB file from volume
```

### Frontend Static Files

Frontend is built into the Docker image. Rebuild to update.

## SSL/TLS Management

### Let's Encrypt (Certbot)

Install Certbot on the host:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate (nginx plugin handles config)
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured by Certbot
```

Or use standalone mode:

```bash
sudo certbot certonly --standalone -d your-domain.com
# Then copy to docker/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem docker/ssl/key.pem
```

### Renewal Automation

Add to crontab:

```bash
0 3 * * * cd /path/to/tact-ai && certbot renew --quiet --deploy-hook "docker-compose -f docker-compose.prod.yml restart nginx"
```

## Security Hardening

1. **Change default passwords**:
   - PostgreSQL: Set `POSTGRES_PASSWORD` to strong random value
   - Grafana: Set `GRAFANA_PASSWORD` env var

2. **Firewall**: Only expose ports 80 and 443 to the internet

3. **Secrets Management**:
   - Use Docker secrets or external secret manager (AWS Secrets Manager, HashiCorp Vault)
   - Never commit `.env` with real secrets

4. **Container Security**:
   - All containers run as non-root users
   - Image scanning (Docker Scout, Trivy) in CI/CD
   - Regular security updates

5. **Network Segmentation**:
   - Internal services (PostgreSQL, Redis) not exposed externally
   - All communication within Docker network

## Troubleshooting

### Services not starting

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs <service-name>

# Common issues:
# - Missing SSL certificates: Ensure docker/ssl/cert.pem and key.pem exist
# - Environment variables: Verify .env file
# - Port conflicts: Check if port 80/443 already in use
```

### Database connection errors

```bash
# Check PostgreSQL health
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# View PostgreSQL logs
docker-compose -f docker-compose.prod.yml logs postgres

# Verify credentials in .env match database
docker-compose -f docker-compose.prod.yml exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
```

### Backend API errors

```bash
# Check backend logs
docker-compose -f docker-compose.prod.yml logs backend

# Test health endpoint
curl https://your-domain.com/health

# Exec into container
docker-compose -f docker-compose.prod.yml exec backend bash
# Inside container, check:
# - Environment variables: env | grep -E "DATABASE|REDIS|OPENAI"
# - Database connectivity: python -c "from backend.database import engine; engine.connect()"
```

### High memory usage

```bash
# Check container resource usage
docker stats

# Backend: Adjust Gunicorn workers (fewer workers = less memory)
# PostgreSQL: Increase shared_buffers in postgresql.conf (requires custom config)
# Redis: Adjust maxmemory setting
```

### Performance issues

```bash
# Enable slow query logging in PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres psql -U tactuser -d tactai -c "ALTER SYSTEM SET log_min_duration_statement = 1000; SELECT pg_reload_conf();"

# Check Prometheus metrics for bottlenecks
# - High database connection count
# - Slow API response times
# - High Redis memory usage

# Profile scheduler performance using built-in benchmarking
curl -X POST "https://your-domain.com/api/scheduler/benchmark" -H "Authorization: Bearer YOUR_TOKEN"
```

### SSL Certificate errors

```bash
# Verify certificate files
ls -la docker/ssl/

# Check certificate validity
openssl x509 -in docker/ssl/cert.pem -text -noout

# Test Nginx config
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
```

### Grafana/Prometheus not accessible

These services are only accessible via their internal Docker network. To access from host:

```bash
# Prometheus metrics API (internal)
# Nginx does not proxy /prometheus by default for security
# Access directly via Docker host:
curl http://localhost:9090/metrics

# Grafana: Change port mapping in docker-compose.prod.yml or access via ssh tunnel
ssh -L 3000:localhost:3000 user@your-server
# Then visit http://localhost:3000
```

## Maintenance

### Updating the Application

1. Pull latest code
2. Rebuild images: `docker-compose -f docker-compose.prod.yml build --no-cache`
3. Run migrations: `docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head`
4. Restart services: `docker-compose -f docker-compose.prod.yml down && docker-compose -f docker-compose.prod.yml up -d`

### Log Rotation

Logs are configured with Docker's json-file driver with rotation:
- Max size: 10MB per file
- Max files: 3 (keeps 30MB total)

Adjust in `docker-compose.prod.yml` under `logging.options`.

### Database Maintenance

```bash
# Vacuum and analyze (weekly recommended)
docker-compose -f docker-compose.prod.yml exec postgres psql -U tactuser -d tactai -c "VACUUM ANALYZE;"

# Rebuild indexes if bloated
docker-compose -f docker-compose.prod.yml exec postgres psql -U tactuser -d tactai -c "REINDEX DATABASE tactai;"
```

### Clearing Redis Cache

```bash
# Flush all data (use with caution!)
docker-compose -f docker-compose.prod.yml exec redis redis-cli FLUSHALL
```

## Monitoring & Alerts

### Grafana Dashboards

Access Grafana at `http://your-domain.com:3001`:

- Login with admin password from `GRAFANA_PASSWORD`
- Pre-provisioned dashboard: "Tact AI Overview"
- Create custom dashboards using Prometheus metrics:
  - `backend_http_requests_total`
  - `backend_http_request_duration_seconds`
  - `backend_scheduler_duration_seconds`
  - `backend_ai_classifier_duration_seconds`

### Setting up Alerts

1. In Grafana, create alert rules:
   - High error rate (>5% 5xx responses)
   - High response times (>2s average)
   - Scheduler duration spike (>30s)

2. Configure notification channels:
   - Email
   - Slack webhook
   - PagerDuty

### Prometheus Retention

Default: 200 hours (~8 days). Adjust in `docker/prometheus.yml`:

```yaml
- '--storage.tsdb.retention.time=720h'  # 30 days
```

Increase disk space for `prometheus_data` volume accordingly.

## Performance Optimization Checklist

- [ ] Enable Gzip compression (already in Nginx)
- [ ] Set Cache-Control headers for static assets (already in Nginx)
- [ ] Add PostgreSQL indexes on frequently queried columns (see `docker/init.sql`)
- [ ] Tune Gunicorn workers based on CPU cores
- [ ] Enable Redis caching for AI classifier (already implemented in code)
- [ ] Configure connection pooling (pgBouncer for PostgreSQL)
- [ ] Enable HTTP/2 (already in Nginx)
- [ ] Use CDN for static assets (optional)
- [ ] Implement rate limiting (already in Nginx)
- [ ] Database query optimization (monitor slow queries in Prometheus)

## Support & Issue Resolution

All issues should be reported via GitHub Issues with:
- Service logs (`docker-compose logs <service>`)
- Error messages
- Steps to reproduce
- Environment details (Docker version, OS)

For urgent production issues:
1. Check service health: `docker-compose ps`
2. Review recent logs: `docker-compose logs --tail=100 <service>`
3. Restart problematic service: `docker-compose restart <service>`
4. Escalate to on-call engineer if unresolved

---

**Last Updated**: 2025-03-12
**Maintainer**: Tact AI Development Team
