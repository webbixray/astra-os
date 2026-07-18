# Quick Start Deployment

Fast path to deploy ASTRA OS to production.

## 1. Prepare (5 minutes)

```bash
# Copy production config
cp docker/prod/.env.example .env.prod

# Edit environment variables
nano .env.prod

# Key variables to set:
# - DOMAIN=your-domain.com
# - POSTGRES_PASSWORD=<strong-password>
# - REDIS_PASSWORD=<strong-password>
# - SECRET_KEY=<64-char-key>
```

## 2. SSL Setup (10 minutes)

### Using Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy to project
mkdir -p docker/prod/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/prod/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem docker/prod/ssl/
sudo chown $USER:$USER docker/prod/ssl/*
```

### Self-Signed (Testing Only)

```bash
./deploy.sh init-ssl
```

## 3. Build Images (15-30 minutes)

```bash
# Build production images
./deploy.sh build

# Or manually
docker build -t astra-api:latest -f apps/api/Dockerfile .
docker build -t astra-web:latest -f apps/web/Dockerfile .
```

## 4. Deploy (5 minutes)

```bash
# Start all services
./deploy.sh up

# Check status
./deploy.sh status

# View logs
./deploy.sh logs
```

## 5. Initialize Database (5 minutes)

```bash
# Run migrations
./deploy.sh migrate

# Check health
curl https://your-domain.com/api/v1/health
```

## Common Commands

```bash
# View all logs
./deploy.sh logs

# View specific service logs
./deploy.sh logs api
./deploy.sh logs web

# Stop services
./deploy.sh down

# Backup database
./deploy.sh backup

# Restore from backup
./deploy.sh restore backup-20240101-120000.sql

# Restart services
docker compose -f docker/prod/docker-compose.yml --env-file .env.prod restart
```

## Verify Deployment

```bash
# All services healthy?
./deploy.sh status

# API responding?
curl https://your-domain.com/api/v1/health

# Web accessible?
curl -I https://your-domain.com

# Database connected?
./deploy.sh logs api | grep -i postgres
```

## Next Steps

- Set up monitoring (Sentry, OpenTelemetry)
- Configure backups (automated daily backups)
- Set up DNS/CDN (CloudFlare, AWS CloudFront)
- Enable automated certificate renewal
- Monitor logs and metrics

## Troubleshooting

```bash
# Container logs
./deploy.sh logs <service>

# Service status
docker compose -f docker/prod/docker-compose.yml --env-file .env.prod ps

# Resource usage
docker stats

# Network connectivity
docker compose -f docker/prod/docker-compose.yml --env-file .env.prod exec api curl http://postgres:5432

# Database connection
docker compose -f docker/prod/docker-compose.yml --env-file .env.prod exec postgres psql -U astra -c "SELECT 1"
```

## Infrastructure Requirements

| Service | CPU | RAM | Storage |
|---------|-----|-----|---------|
| PostgreSQL | 0.5-1 | 512MB | 10GB+ |
| Redis | 0.25 | 256MB | 1GB |
| Temporal | 0.5 | 512MB | 5GB |
| API | 1-2 | 1GB | - |
| Web | 0.5-1 | 512MB | - |
| Nginx | 0.25 | 256MB | - |
| **Total** | **4-6** | **3-4GB** | **20GB+** |

## Deployment Checklist

- [ ] Environment variables configured (.env.prod)
- [ ] SSL certificates in place
- [ ] Domain DNS points to server
- [ ] Firewall allows 80/443
- [ ] Disk space available (20GB+)
- [ ] Docker and Compose installed
- [ ] Images built successfully
- [ ] Services started with `./deploy.sh up`
- [ ] All health checks passing
- [ ] Database migrations applied
- [ ] API responds to health checks
- [ ] Web application loads in browser
- [ ] Backups tested and working

