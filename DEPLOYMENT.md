# ASTRA OS - Deployment Guide

This guide covers deploying ASTRA OS to production using Docker and Docker Compose.

## Architecture Overview

ASTRA OS consists of:
- **PostgreSQL 16** - Primary database
- **Redis 7** - Caching and session store
- **Temporal 1.24** - Workflow orchestration
- **API (FastAPI)** - Python backend on port 8000
- **Web (Next.js)** - Frontend on port 3000
- **Nginx 1.27** - Reverse proxy with SSL/TLS

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- SSL certificates for your domain (Let's Encrypt recommended)
- At least 4GB RAM available
- 20GB free disk space

## Step 1: Prepare Environment

```bash
# Clone the repository
git clone <your-repo> astra-os
cd astra-os

# Copy production environment template
cp docker/prod/.env.example .env.prod

# Edit with your values
nano .env.prod
```

### Required Environment Variables

```bash
# Database - Generate strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

# Security - Generate a 64-character secret key
SECRET_KEY=$(openssl rand -hex 32)

# Domain configuration
DOMAIN=your-domain.com

# Optional: Observability
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Optional: Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## Step 2: Configure SSL Certificates

### Option A: Using Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy certificates to docker/prod/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/prod/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem docker/prod/ssl/
sudo chown $USER:$USER docker/prod/ssl/*
```

### Option B: Self-Signed Certificate (Testing Only)

```bash
mkdir -p docker/prod/ssl
openssl req -x509 -newkey rsa:4096 -nodes \
  -out docker/prod/ssl/fullchain.pem \
  -keyout docker/prod/ssl/privkey.pem \
  -days 365 \
  -subj "/CN=your-domain.com"
```

## Step 3: Configure Nginx

Edit `docker/prod/nginx.conf`:

```nginx
# Replace DOMAIN with your actual domain
server_name your-domain.com www.your-domain.com;

# Update upstream addresses if needed
upstream api_backend {
    server api:8000;
}

upstream web_backend {
    server web:3000;
}
```

## Step 4: Build Production Images

```bash
# Build API image
docker build -t astra-api:latest -f apps/api/Dockerfile .

# Build Web image
docker build -t astra-web:latest -f apps/web/Dockerfile .

# Optionally, tag for registry (e.g., Docker Hub, ECR)
docker tag astra-api:latest your-registry/astra-api:1.0.0
docker tag astra-web:latest your-registry/astra-web:1.0.0
docker push your-registry/astra-api:1.0.0
docker push your-registry/astra-web:1.0.0
```

## Step 5: Deploy with Docker Compose

```bash
# Navigate to production directory
cd docker/prod

# Start services
docker compose --env-file ../../.env.prod up -d

# Verify all services are healthy
docker compose ps

# Check logs
docker compose logs -f

# View specific service logs
docker compose logs api
docker compose logs web
docker compose logs postgres
```

## Step 6: Database Initialization

```bash
# Run migrations
docker compose exec -T api python -m alembic upgrade head

# Seed data (if applicable)
docker compose exec -T api python -m scripts.seed_db

# Create backups directory
docker compose exec postgres mkdir -p /var/lib/postgresql/backups
```

## Step 7: Verify Deployment

```bash
# Check API health
curl https://your-domain.com/api/v1/health

# Check Web health
curl https://your-domain.com/api/health

# Verify all containers are running
docker compose ps

# Check resource usage
docker stats

# Monitor logs
docker compose logs -f --tail=100
```

## Health Checks

All services have health checks configured:

- **PostgreSQL**: `pg_isready -U astra` (10s interval, 5 retries)
- **Redis**: `redis-cli -a $PASSWORD ping` (10s interval, 5 retries)
- **Temporal**: Cluster health check (10s interval, 10 retries)
- **API**: HTTP GET `/api/v1/health/live` (15s interval, 3 retries)
- **Web**: HTTP HEAD `/api/health` (15s interval, 3 retries)
- **Nginx**: HTTP HEAD `/api/v1/health` (15s interval, 3 retries)

## Resource Limits

Production deployment includes resource limits:

```
API:          1-2 CPU cores, 1GB RAM
Web:          0.5-1 CPU core, 512MB RAM
PostgreSQL:   0.5-1 CPU core, 512MB RAM
Redis:        0.25-0.5 CPU core, 256MB RAM
Nginx:        0.25-0.5 CPU core, 256MB RAM
```

Adjust in `docker/prod/docker-compose.yml` based on your infrastructure.

## Persistence

Data volumes:

- **pgdata**: PostgreSQL data (`/var/lib/postgresql/data`)
- **redis_data**: Redis persistence (`/data`)

Backup strategy:

```bash
# Backup PostgreSQL
docker compose exec postgres pg_dump -U astra astra > backup-$(date +%Y%m%d-%H%M%S).sql

# Restore from backup
docker compose exec -T postgres psql -U astra astra < backup.sql
```

## Monitoring & Logging

### JSON Logging

All containers log to JSON format with rotation:
- Max file size: 10MB
- Max files: 3

View logs:
```bash
# All services
docker compose logs

# Follow logs
docker compose logs -f

# Specific service
docker compose logs api --tail=100

# With timestamps
docker compose logs --timestamps
```

### Optional: Sentry Integration

If `SENTRY_DSN` is set, errors are automatically reported to Sentry.

### Optional: OpenTelemetry Integration

API supports OpenTelemetry (OTLP) for distributed tracing. Configure `OTLP_ENDPOINT`.

## Security Hardening

Production deployment includes:

- **Non-root users**: API runs as `astra` (65532:65532), Web as `nextjs` (1001:1001)
- **Read-only filesystem**: `/` is read-only; only `/tmp` and `/var/cache` are writable
- **No new privileges**: `security_opt: no-new-privileges:true`
- **Resource limits**: CPU and memory capped
- **SSL/TLS**: All traffic encrypted with certificates
- **Environment-based secrets**: All secrets loaded from `.env.prod`, never baked into images
- **Healthchecks**: Automatic recovery of failed services

## Scaling & Orchestration

### Multi-node Deployment

For high availability, use Docker Swarm or Kubernetes:

```bash
# Docker Swarm
docker swarm init
docker stack deploy -c docker/prod/docker-compose.yml astra

# Kubernetes (see k8s/ directory)
kubectl apply -f k8s/
```

### Auto-scaling

Adjust replica counts in Swarm/K8s manifests as needed.

## Maintenance

### Updates

```bash
# Pull latest images
docker pull postgres:16-alpine
docker pull redis:7-alpine
docker pull temporalio/auto-setup:1.24

# Rebuild application images
docker build -t astra-api:latest -f apps/api/Dockerfile .
docker build -t astra-web:latest -f apps/web/Dockerfile .

# Restart services (rolling update)
docker compose up -d
```

### Database Migrations

```bash
# Before deployment
docker compose exec api python -m alembic current
docker compose exec api python -m alembic upgrade head

# Rollback (if needed)
docker compose exec api python -m alembic downgrade -1
```

### Certificate Renewal (Let's Encrypt)

```bash
# Automated renewal (add to crontab)
0 3 * * * certbot renew --quiet && \
  cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /path/to/docker/prod/ssl/ && \
  cp /etc/letsencrypt/live/your-domain.com/privkey.pem /path/to/docker/prod/ssl/ && \
  docker compose -f /path/to/docker/prod/docker-compose.yml restart nginx
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker compose logs <service>

# Inspect the container
docker compose exec <service> sh

# Restart service
docker compose restart <service>
```

### Database connection errors

```bash
# Check PostgreSQL is healthy
docker compose exec postgres pg_isready -U astra

# Check connection string in API
docker compose exec api env | grep DATABASE_URL

# Test connection manually
docker compose exec postgres psql -U astra -c "SELECT 1"
```

### Out of memory

```bash
# Check current usage
docker stats

# Increase memory limit in docker-compose.yml
# Then restart: docker compose down && docker compose up -d
```

### Disk space issues

```bash
# Check disk usage
docker system df

# Clean up unused images/volumes
docker system prune --volumes
```

## Rollback Procedure

```bash
# Save current state
docker compose down
tar czf backup-$(date +%Y%m%d-%H%M%S).tar.gz \
  docker/prod/ .env.prod

# Restore from backup
tar xzf backup-timestamp.tar.gz

# Restart
docker compose up -d
```

## Support

For issues or questions:
- Check logs: `docker compose logs -f`
- Review health: `docker compose ps`
- Inspect containers: `docker inspect <container>`
- Visit docs: https://docs.docker.com/

