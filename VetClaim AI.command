#!/bin/bash
# VetClaim AI — Desktop launcher
# Double-click this file to start all servers and open the app in your browser.

ROOT="/Users/ismai/hackathon/vetclaim"
PYTHON="/opt/anaconda3/bin/python3"

# ── Cleanup on exit ─────────────────────────────────────────
cleanup() {
  echo ""
  echo "Stopping all VetClaim AI services..."
  jobs -p | xargs -r kill 2>/dev/null
  wait 2>/dev/null
  echo "All services stopped."
  exit 0
}
trap cleanup INT TERM

# ── Kill anything already on these ports ────────────────────
for port in 5001 5050 5173; do
  pids=$(lsof -t -i:$port 2>/dev/null)
  [ -n "$pids" ] && echo "Clearing port $port..." && echo "$pids" | xargs kill -9 2>/dev/null && sleep 0.5
done

echo "Starting Backend API    → http://localhost:5001"
(cd "$ROOT/backend" && $PYTHON server.py 2>&1 | sed 's/^/[backend]   /') &

echo "Starting Mock VA Portal → http://localhost:5050"
(cd "$ROOT/mock_va_portal" && $PYTHON server.py 2>&1 | sed 's/^/[va-portal] /') &

echo "Starting Frontend       → http://localhost:5173"
(cd "$ROOT/frontend" && npm run dev 2>&1 | sed 's/^/[frontend]  /') &

# ── Wait for servers to be ready, then open browsers ────────
echo "Waiting for servers to start..."
for url in "http://localhost:5001" "http://localhost:5050" "http://localhost:5173"; do
  for i in $(seq 1 20); do
    curl -s -o /dev/null "$url" && break
    sleep 1
  done
done

echo "Opening browsers..."
open "http://localhost:5173"
open "http://localhost:5050"

echo ""
echo "VetClaim AI is running. Close this window to stop all services."
wait
