#!/bin/bash
set -a
source /home/ubuntu/agent-hackthon/.env.hackathon
set +a
cd /home/ubuntu/agent-hackthon/backend
exec python3 -m uvicorn api:app --host 0.0.0.0 --port 8001
