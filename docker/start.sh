#!/bin/bash
# AiDiy2026 Docker Startup Script

set -e  # Exit on error

echo "=========================================="
echo "  AiDiy2026 Starting..."
echo "=========================================="

cd /app

# Start Backend Core API (main1) in background
echo "[1/3] Starting Backend Core API (port 8091)..."
cd /app/backend_server
python -m uvicorn main1:app --host 0.0.0.0 --port 8091 --log-level info &
CORE_PID=$!
sleep 2

# Start Backend Apps API (main2) in background
echo "[2/3] Starting Backend Apps API (port 8092)..."
python -m uvicorn main2:app --host 0.0.0.0 --port 8092 --log-level info &
APPS_PID=$!
sleep 2

# Start Frontend server with simple HTTP server
echo "[3/3] Starting Frontend (port 8090)..."
cd /app/frontend_server/dist
python -m http.server 8090 &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "  AiDiy2026 Started Successfully!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - Frontend:    http://localhost:8090"
echo "  - Core API:    http://localhost:8091/docs"
echo "  - Apps API:    http://localhost:8092/docs"
echo ""
echo "Default Login:"
echo "  - Username: admin"
echo "  - Password: (check README.md)"
echo ""
echo "Press Ctrl+C to stop all services..."
echo ""

# Trap SIGTERM and SIGINT to gracefully stop all processes
trap "echo 'Stopping services...'; kill $CORE_PID $APPS_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGTERM SIGINT

# Wait for all background processes
wait $CORE_PID $APPS_PID $FRONTEND_PID
