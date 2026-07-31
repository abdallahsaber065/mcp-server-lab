#!/usr/bin/env bash
# deploy.sh — pull latest image from GHCR and restart container
set -e

REPO_DIR="/opt/mcp-server-lab"
cd "$REPO_DIR"

echo "==> Fetching latest git changes..."
git fetch origin
git reset --hard origin/master
git clean -fd

echo "==> Pulling latest Docker image from GHCR..."
docker compose pull

echo "==> Restarting container..."
docker compose up -d --remove-orphans

echo "==> Pruning unused images..."
docker image prune -f

echo "==> Waiting for app to come up..."
sleep 3
curl -sf http://127.0.0.1:8011/ > /dev/null && echo "✅ App is up at http://127.0.0.1:8011/" || echo "❌ App not responding on port 8011"
