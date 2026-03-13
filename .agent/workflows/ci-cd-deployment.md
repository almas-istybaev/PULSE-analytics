---
description: How to deploy the application and configure CI/CD pipelines
---

# Continuous Integration & Deployment (CI/CD) Pipeline

This project uses a direct SSH deployment model for rapid iteration. When code is pushed to the `main` branch, the deployment process updates the target VPS.

## 1. Manual Deployment Steps (Prod)
If you need to deploy manually to the production server.

```bash
# 1. SSH into the server
ssh [user]@[production_ip]

# 2. Navigate to project root
cd /path/to/inventory-monitor

# 3. Pull latest code
git pull origin main

# 4. Ensure Docker services are running (MinIO)
docker compose up -d minio

# 5. Apply database migrations
source venv/bin/activate
alembic upgrade head

# 6. Rebuild frontend (If React code changed)
cd client
npm install
npm run build
cd ..

# 7. Restart the FastAPI backend daemon
pm2 restart inventory-api
```

## 2. Automated CI/CD (GitHub Actions / Bitbucket Pipelines)

To completely automate this, set up a pipeline YAML that triggers on push to `main`:

```yaml
# Example snippet for CI/CD
steps:
  - step:
      name: Deploy to Production
      deployment: production
      script:
        - ssh $PROD_USER@$PROD_HOST "cd /path/to/inventory-monitor && git pull origin main && docker compose up -d minio && source venv/bin/activate && pip install -r requirements.txt && alembic upgrade head && cd client && npm install && npm run build && pm2 restart inventory-api"
```

## 3. Infrastructure Architecture

- **Nginx Reverse Proxy:** Serves the built Vue/React assets from `client/dist` and proxies `/api` requests to `localhost:8000`.
- **FastAPI / Uvicorn:** Runs as a managed daemon (e.g., PM2 or systemd) mapping to `localhost:8000`.
- **MinIO Backup/Restore:** Persistent volumes are mapped securely using `docker-compose.yml`. Ensure `.env` files are not version controlled.
