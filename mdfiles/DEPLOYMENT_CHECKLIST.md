# Deployment Checklist

## Pre-Deployment

- [ ] Obtain Gemini API key from https://aistudio.google.com/app/apikey
- [ ] Have PubMed access email ready
- [ ] Install Docker and Docker Compose
- [ ] Clone repository to deployment server

## Configuration

- [ ] Copy `env.example` to `.env`
- [ ] Add `GEMINI_API_KEY` to `.env`
- [ ] Add `PUBMED_EMAIL` to `.env`
- [ ] Review `docker-compose.yml` for any custom settings
- [ ] Set appropriate resource limits if needed

## Build & Deploy

- [ ] Run `docker-compose build` to build images
- [ ] Run `docker-compose up -d` to start services
- [ ] Wait for health checks to pass (check with `docker-compose ps`)
- [ ] Verify backend: `curl http://localhost:8000/health`
- [ ] Verify frontend: `curl http://localhost:3000`

## Testing

- [ ] Access frontend at http://localhost:3000
- [ ] Submit a test research request
- [ ] Verify PubMed search works (requires email)
- [ ] Check that results display correctly
- [ ] Test export functionality
- [ ] Review backend logs: `docker-compose logs backend`
- [ ] Review frontend logs: `docker-compose logs frontend`

## Production Configuration (Optional)

- [ ] Set up reverse proxy (Nginx/Traefik)
- [ ] Configure SSL/HTTPS with Let's Encrypt
- [ ] Set up domain name
- [ ] Configure firewall rules
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure log aggregation
- [ ] Set up automated backups for database
- [ ] Configure rate limiting
- [ ] Set up alerts for service health

## Security Hardening

- [ ] Never commit `.env` file
- [ ] Use Docker secrets in production
- [ ] Run containers as non-root user
- [ ] Enable Docker content trust
- [ ] Regularly update base images
- [ ] Scan images for vulnerabilities
- [ ] Use private Docker registry
- [ ] Implement API rate limiting
- [ ] Set up WAF if public-facing

## Monitoring

- [ ] Set up health check monitoring
- [ ] Configure resource usage alerts
- [ ] Set up log monitoring
- [ ] Track API response times
- [ ] Monitor disk usage for database
- [ ] Set up uptime monitoring

## Maintenance

- [ ] Schedule regular database backups
- [ ] Plan for log rotation
- [ ] Keep Docker images updated
- [ ] Monitor and clean unused Docker resources
- [ ] Review and update dependencies monthly
- [ ] Test disaster recovery procedures

## Documentation

- [ ] Document custom configuration
- [ ] Create runbook for common issues
- [ ] Document backup/restore procedures
- [ ] Create incident response plan
- [ ] Document scaling procedures

## Post-Deployment

- [ ] Test all major features
- [ ] Monitor logs for errors
- [ ] Check resource usage
- [ ] Verify database persistence
- [ ] Test container restart recovery
- [ ] Verify health checks are working
- [ ] Document any issues encountered
- [ ] Share access credentials securely with team

## Rollback Plan

- [ ] Keep previous Docker images tagged
- [ ] Document rollback procedure
- [ ] Test rollback in staging
- [ ] Have database backup ready

## Quick Commands Reference

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Logs
docker-compose logs -f

# Restart
docker-compose restart

# Rebuild
docker-compose up --build -d

# Health check
docker-compose ps
docker inspect --format='{{.State.Health.Status}}' research-agent-backend
docker inspect --format='{{.State.Health.Status}}' research-agent-frontend

# Database backup
docker run --rm -v research-agent_backend-db:/data -v $(pwd):/backup alpine tar -czf /backup/db-backup.tar.gz -C /data .

# Clean everything
docker-compose down -v
docker system prune -a
```

## Support Contacts

- Technical Lead: [Name/Email]
- DevOps: [Name/Email]
- On-Call: [Phone/Pager]

## Notes

- Default ports: Frontend (3000), Backend (8000)
- Database: SQLite (stored in Docker volume)
- Health checks: 30s interval, 40s start period
- Auto-restart: enabled (unless-stopped)

