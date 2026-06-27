#!/usr/bin/env bash
# Package GrowEngine for a clean hackathon/server deployment.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT_DIR="$PROJECT_ROOT/dist"
PACKAGE_NAME="growengine-agent-hackathon-$STAMP.tar.gz"
PACKAGE_PATH="$OUT_DIR/$PACKAGE_NAME"

mkdir -p "$OUT_DIR"

tar \
  --exclude='.git' \
  --exclude='.github' \
  --exclude='.vscode' \
  --exclude='dist' \
  --exclude='data' \
  --exclude='Simple_Tiktok_App' \
  --exclude='ad_rec_backend' \
  --exclude='ad_rec_frontend' \
  --exclude='web_visualization' \
  --exclude='backend/saved_model' \
  --exclude='**/node_modules' \
  --exclude='**/venv' \
  --exclude='**/__pycache__' \
  --exclude='**/.pytest_cache' \
  --exclude='**/.DS_Store' \
  --exclude='.env.hackathon' \
  -czf "$PACKAGE_PATH" \
  .

echo "Package created:"
echo "$PACKAGE_PATH"
echo "This is the lean server package for the core Agent demo."
echo
echo "Server quick start:"
echo "  tar -xzf $PACKAGE_NAME -C growengine-agent"
echo "  cd growengine-agent"
echo "  cp .env.hackathon.example .env.hackathon"
echo "  docker compose --env-file .env.hackathon -f docker-compose.hackathon.yml up -d --build"
