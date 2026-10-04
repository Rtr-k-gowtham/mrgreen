#!/usr/bin/env bash
# ==============================================================================
# MR.GREEN — Production VPS Deployment Script
# ==============================================================================
set -e

# Ensure standard system PATH is loaded for non-login/SSH shells
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

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

# Build frontend if node/npm is installed on the host
if command -v npm > /dev/null 2>&1 && [ -d "frontend" ]; then
  echo "📦 Building frontend application..."
  (cd frontend && npm install && npm run build) || true
  mkdir -p backend/static
  cp -r frontend/dist/* backend/static/ || true
fi

# Rebuild and restart containers
echo "🐳 Rebuilding and starting Docker services..."
docker compose pull || true
docker compose up -d --build --remove-orphans

# Clean up dangling images to save VPS disk space
echo "🧹 Cleaning up unused Docker images..."
docker image prune -f

# Ensure port 8000 is open in firewall for mobile browser access
if command -v ufw > /dev/null 2>&1; then
  echo "🔓 Ensuring firewall allows port 8000 for mobile web access..."
  ufw allow 8000/tcp || true
fi
if command -v iptables > /dev/null 2>&1; then
  iptables -I INPUT -p tcp --dport 8000 -j ACCEPT || true
fi

# Configure Nginx reverse proxy on port 80 to route public web & mobile requests to MR.GREEN
if command -v nginx > /dev/null 2>&1 && [ -d "/etc/nginx" ]; then
  echo "🌐 Configuring Nginx reverse proxy for MR.GREEN on port 80..."
  mkdir -p /etc/nginx/conf.d
  cat > /etc/nginx/conf.d/mrgreen.conf << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
  if [ -f /etc/nginx/sites-enabled/default ]; then
    rm -f /etc/nginx/sites-enabled/default || true
  fi
  nginx -t && (systemctl reload nginx || service nginx reload) || echo "Nginx reload skipped"
fi

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
