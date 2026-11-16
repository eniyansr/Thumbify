#!/usr/bin/env bash
set -e

echo "============================================================"
echo "  THUMBIFY — Remote VPS Deployment Setup"
echo "============================================================"

# Ensure Docker is installed
if ! command -v docker &> /dev/null; then
    echo "[INFO] Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm -f get-docker.sh
fi

# Ensure Docker Compose plugin or standalone is available
if ! docker compose version &> /dev/null; then
    echo "[INFO] Installing Docker Compose plugin..."
    apt-get update && apt-get install -y docker-compose-plugin || true
fi

# Stop existing container if running
echo "[INFO] Stopping previous instances if any..."
docker compose down || true

# Build and start container in detached mode
echo "[INFO] Building and starting THUMBIFY container..."
docker compose up -d --build

# Wait a moment and check status
sleep 3
echo "============================================================"
echo "  Container Status:"
echo "============================================================"
docker compose ps

echo ""
echo "[INFO] Viewing initial logs:"
docker compose logs --tail 20

echo ""
echo "============================================================"
echo " [SUCCESS] THUMBIFY is now running 24/7 on your cloud server!"
echo " You can now close your laptop safely."
echo "============================================================"
