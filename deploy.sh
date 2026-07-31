#!/usr/bin/env bash
# deploy.sh — pull latest from GitHub and rebuild/restart the container
# Usage: ssh ubuntu@98.80.23.115 "bash /opt/mcp-server-lab/deploy.sh"

set -e

REPO_DIR="/opt/mcp-server-lab"
cd "$REPO_DIR"

echo "==> Fetching latest from GitHub..."
git fetch origin
git reset --hard origin/master
git clean -fd

echo "==> Rebuilding Docker image..."
docker compose build

echo "==> Restarting container..."
docker compose up -d

echo "==> Waiting for app to come up..."
sleep 3
curl -sf http://127.0.0.1:8011/ > /dev/null && echo "✅ App is up at http://127.0.0.1:8011/" || echo "❌ App not responding on port 8011"
