#!/usr/bin/env bash
# ==============================================================================
# MR.GREEN — Production VPS Deployment Script
# ==============================================================================
set -e

echo "🌿 [MR.GREEN] Starting Deployment..."

# Navigate to project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "📂 Project root: $PROJECT_ROOT"

# Ensure environment file exists
if [ ! -f .env ]; then
  if [ -f backend/.env.example ]; then
    echo "⚠️  No .env found, copying from backend/.env.example..."
    cp backend/.env.example .env
  else
    echo "⚠️  Creating baseline .env file..."
    touch .env
  fi
fi

# Pull latest changes from git
echo "📥 Pulling latest changes from origin/main..."
git fetch origin main
git reset --hard origin/main

# Rebuild and restart containers
echo "🐳 Rebuilding and starting Docker services..."
docker compose pull || true
docker compose up -d --build --remove-orphans

# Clean up dangling images to save VPS disk space
echo "🧹 Cleaning up unused Docker images..."
docker image prune -f

# Verify backend health
echo "🩺 Waiting for service healthcheck..."
MAX_RETRIES=15
COUNTER=0
HEALTHY=false

while [ $COUNTER -lt $MAX_RETRIES ]; do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    HEALTHY=true
    break
  fi
  echo "   Waiting for API to be ready... ($((COUNTER + 1))/$MAX_RETRIES)"
  sleep 3
  COUNTER=$((COUNTER + 1))
done

if [ "$HEALTHY" = true ]; then
  echo "✅ [MR.GREEN] Successfully deployed and healthy!"
else
  echo "⚠️  [MR.GREEN] Warning: Health check did not respond in time. Checking container logs:"
  docker compose logs backend --tail 30
  exit 1
fi
