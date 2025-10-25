# Docker Deployment Guide

This guide explains how to deploy the Research Agent application using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 2GB of free disk space
- Gemini API key from Google AI Studio

## Quick Start

### 1. Set Up Environment Variables

Copy the example environment file and fill in your API keys:

```bash
cp env.example .env
```

Edit `.env` and add your credentials:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
PUBMED_EMAIL=your_email@example.com
```

### 2. Build and Run

```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Docker Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### Rebuild Services
```bash
docker-compose up --build -d
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart a Service
```bash
docker-compose restart backend
docker-compose restart frontend
```

### Execute Commands in Container
```bash
# Backend shell
docker-compose exec backend /bin/bash

# Frontend shell
docker-compose exec frontend /bin/sh
```

## Volume Management

### Database Persistence

The backend database is stored in a Docker volume named `backend-db`. To back it up:

```bash
# Create backup
docker run --rm -v research-agent_backend-db:/data -v $(pwd):/backup alpine \
  tar -czf /backup/db-backup-$(date +%Y%m%d).tar.gz -C /data .

# Restore backup
docker run --rm -v research-agent_backend-db:/data -v $(pwd):/backup alpine \
  tar -xzf /backup/db-backup-YYYYMMDD.tar.gz -C /data
```

### Clean Up Volumes

```bash
# Remove all volumes (WARNING: This deletes the database!)
docker-compose down -v
```

## Development Mode

For development with hot reload:

```bash
# Backend with volume mount for live code changes
docker-compose up backend

# Frontend with volume mount
docker-compose up frontend
```

The compose file already mounts the source code directories, so changes will be reflected immediately.

## Production Deployment

### 1. Build for Production

```bash
# Remove --reload flag from backend Dockerfile CMD
# Update frontend to use production build

docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 2. Use a Reverse Proxy

It's recommended to use Nginx or Traefik as a reverse proxy:

```nginx
# Example Nginx config
server {
    listen 80;
    server_name research-agent.example.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Enable HTTPS

Use Let's Encrypt with certbot:

```bash
sudo certbot --nginx -d research-agent.example.com
```

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Missing GEMINI_API_KEY
# - Port 8000 already in use
# - Database permission issues
```

### Frontend Build Fails

```bash
# Check logs
docker-compose logs frontend

# Common issues:
# - Node modules not installing (try: docker-compose build --no-cache frontend)
# - Out of memory (increase Docker memory limit)
```

### Database Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d

# Check database file
docker-compose exec backend ls -la /app/research_agent.db
```

### Network Issues

```bash
# Check if services can communicate
docker-compose exec frontend ping backend
docker-compose exec backend ping frontend

# Restart network
docker-compose down
docker-compose up -d
```

## Monitoring

### Health Checks

Both services have health checks configured:

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' research-agent-backend
docker inspect --format='{{.State.Health.Status}}' research-agent-frontend
```

### Resource Usage

```bash
# Monitor resource usage
docker stats research-agent-backend research-agent-frontend
```

## Security Best Practices

1. **Never commit `.env` file** - It contains sensitive API keys
2. **Use secrets management** in production (Docker Swarm secrets, Kubernetes secrets)
3. **Run as non-root** - Frontend already configured, backend should follow
4. **Regular updates** - Keep base images and dependencies updated
5. **Network isolation** - Use Docker networks to isolate services
6. **Read-only filesystem** where possible

## Scaling

To run multiple backend instances:

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
```

Then use a load balancer like Nginx or HAProxy to distribute traffic.

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build images
        run: docker-compose build
      - name: Push to registry
        run: |
          docker tag research-agent-backend:latest your-registry/backend:latest
          docker push your-registry/backend:latest
```

## Support

For issues and questions:
- Check logs: `docker-compose logs`
- Restart services: `docker-compose restart`
- Clean rebuild: `docker-compose down && docker-compose up --build -d`

