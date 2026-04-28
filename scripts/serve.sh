#!/usr/bin/env bash
#
# start.sh - Start all MedrixFlow development services
#
# Must be run from the repo root directory.

set -e

export PATH="$HOME/.local/bin:$PATH"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# ── Argument parsing ─────────────────────────────────────────────────────────

DEV_MODE=true
for arg in "$@"; do
    case "$arg" in
        --dev)  DEV_MODE=true ;;
        --prod) DEV_MODE=false ;;
        *) echo "Unknown argument: $arg"; echo "Usage: $0 [--dev|--prod]"; exit 1 ;;
    esac
done

if $DEV_MODE; then
    FRONTEND_CMD="pnpm run dev"
else
    FRONTEND_CMD="env BETTER_AUTH_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(16))') pnpm run preview"
fi

# ── Stop existing services ────────────────────────────────────────────────────

echo "Stopping existing services if any..."
pkill -f "langgraph dev" 2>/dev/null || true
pkill -f "uvicorn app.gateway.app:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
pkill -f "next-server" 2>/dev/null || true
nginx -c "$REPO_ROOT/docker/nginx/nginx.local.conf" -p "$REPO_ROOT" -s quit 2>/dev/null || true
sleep 1
pkill -9 nginx 2>/dev/null || true
killall -9 nginx 2>/dev/null || true
lsof -ti :2024 | xargs kill -9 2>/dev/null || true
lsof -ti :8001 | xargs kill -9 2>/dev/null || true
lsof -ti :3000 | xargs kill -9 2>/dev/null || true
./scripts/cleanup-containers.sh medrix-flow-sandbox 2>/dev/null || true
sleep 1

# ── Banner ────────────────────────────────────────────────────────────────────

echo ""
echo "=========================================="
echo "  Starting MedrixFlow Development Server"
echo "=========================================="
echo ""
if $DEV_MODE; then
    echo "  Mode: DEV  (hot-reload enabled)"
    echo "  Tip:  run \`make start\` in production mode"
else
    echo "  Mode: PROD (hot-reload disabled)"
    echo "  Tip:  run \`make dev\` to start in development mode"
fi
echo ""
echo "Services starting up..."
echo "  → Backend: LangGraph + Gateway"
echo "  → Frontend: Next.js"
echo "  → Nginx: Reverse Proxy"
echo ""

# ── Config check ─────────────────────────────────────────────────────────────

if ! { \
        [ -n "$MEDRIX_FLOW_CONFIG_PATH" ] && [ -f "$MEDRIX_FLOW_CONFIG_PATH" ] || \
        [ -f backend/config.yaml ] || \
        [ -f config.yaml ]; \
    }; then
    echo "✗ No MedrixFlow config file found."
    echo "  Checked these locations:"
    echo "    - $MEDRIX_FLOW_CONFIG_PATH (when MEDRIX_FLOW_CONFIG_PATH is set)"
    echo "    - backend/config.yaml"
    echo "    - ./config.yaml"
    echo ""
    echo "  Run 'make config' from the repo root to generate ./config.yaml, then set required model API keys in .env or your config file."
    exit 1
fi

# ── Auto-upgrade config ──────────────────────────────────────────────────

"$REPO_ROOT/scripts/config-upgrade.sh"

# ── Cleanup trap ─────────────────────────────────────────────────────────────

cleanup() {
    trap - INT TERM
    echo ""
    echo "Shutting down services..."
    pkill -f "langgraph dev" 2>/dev/null || true
    pkill -f "uvicorn app.gateway.app:app" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true
    pkill -f "next start" 2>/dev/null || true
    pkill -f "next-server" 2>/dev/null || true
    # Kill nginx using the captured PID first (most reliable),
    # then fall back to pkill/killall for any stray nginx workers.
    if [ -n "${NGINX_PID:-}" ] && kill -0 "$NGINX_PID" 2>/dev/null; then
        kill -TERM "$NGINX_PID" 2>/dev/null || true
        sleep 1
        kill -9 "$NGINX_PID" 2>/dev/null || true
    fi
    pkill -9 nginx 2>/dev/null || true
    killall -9 nginx 2>/dev/null || true
    lsof -ti :2024 | xargs kill -9 2>/dev/null || true
    lsof -ti :8001 | xargs kill -9 2>/dev/null || true
    lsof -ti :3000 | xargs kill -9 2>/dev/null || true
    echo "Cleaning up sandbox containers..."
    ./scripts/cleanup-containers.sh medrix-flow-sandbox 2>/dev/null || true
    echo "✓ All services stopped"
    exit 0
}
trap cleanup INT TERM

# ── Start services ────────────────────────────────────────────────────────────

mkdir -p logs

if $DEV_MODE; then
    LANGGRAPH_EXTRA_FLAGS=""
    GATEWAY_EXTRA_FLAGS="--reload --reload-include='*.yaml' --reload-include='.env'"
else
    LANGGRAPH_EXTRA_FLAGS="--no-reload"
    GATEWAY_EXTRA_FLAGS=""
fi

# Launch LangGraph, Gateway, and Frontend in parallel for faster startup.
# All three are independent at startup time — no inter-service dependency
# until runtime requests flow through Nginx.

echo "Starting LangGraph + Gateway + Frontend in parallel..."

(cd backend && NO_COLOR=1 uv run langgraph dev --no-browser --allow-blocking $LANGGRAPH_EXTRA_FLAGS > ../logs/langgraph.log 2>&1) &
(cd backend && PYTHONPATH=. uv run uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001 $GATEWAY_EXTRA_FLAGS > ../logs/gateway.log 2>&1) &
(cd frontend && $FRONTEND_CMD > ../logs/frontend.log 2>&1) &

# Wait for all three services to become ready (max 120s — longest is Frontend)

LANGGRAPH_READY=false
GATEWAY_READY=false
FRONTEND_READY=false
TIMEOUT=120
elapsed=0
interval=1

while [ "$elapsed" -lt "$TIMEOUT" ]; do
    if ! $LANGGRAPH_READY && lsof -nP -iTCP:2024 -sTCP:LISTEN -t >/dev/null 2>&1; then
        LANGGRAPH_READY=true
        echo "  ✓ LangGraph ready on localhost:2024 (${elapsed}s)"
    fi
    if ! $GATEWAY_READY && lsof -nP -iTCP:8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
        GATEWAY_READY=true
        echo "  ✓ Gateway ready on localhost:8001 (${elapsed}s)"
    fi
    if ! $FRONTEND_READY && lsof -nP -iTCP:3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        FRONTEND_READY=true
        echo "  ✓ Frontend ready on localhost:3000 (${elapsed}s)"
    fi
    if $LANGGRAPH_READY && $GATEWAY_READY && $FRONTEND_READY; then
        break
    fi
    printf "\r  Waiting for services... %ds" "$elapsed"
    sleep "$interval"
    elapsed=$((elapsed + interval))
done
printf "\r  %-60s\r" ""

# Check for failures and report diagnostics
FAILED=false
if ! $LANGGRAPH_READY; then
    FAILED=true
    echo "✗ LangGraph failed to start on port 2024 after ${TIMEOUT}s"
    echo "  See logs/langgraph.log for details"
    tail -20 logs/langgraph.log
    if grep -qE "config_version|outdated|Environment variable .* not found|KeyError|ValidationError|config\.yaml" logs/langgraph.log 2>/dev/null; then
        echo ""
        echo "  Hint: This may be a configuration issue. Try running 'make config-upgrade' to update your config.yaml."
    fi
fi
if ! $GATEWAY_READY; then
    FAILED=true
    echo "✗ Gateway API failed to start on port 8001 after ${TIMEOUT}s"
    tail -60 logs/gateway.log
    echo ""
    echo "Likely configuration errors:"
    grep -E "Failed to load configuration|Environment variable .* not found|config\.yaml.*not found" logs/gateway.log | tail -5 || true
    echo ""
    echo "  Hint: Try running 'make config-upgrade' to update your config.yaml with the latest fields."
fi
if ! $FRONTEND_READY; then
    FAILED=true
    echo "✗ Frontend failed to start on port 3000 after ${TIMEOUT}s"
    echo "  See logs/frontend.log for details"
    tail -20 logs/frontend.log
fi
if $FAILED; then
    cleanup
fi

echo "Starting Nginx reverse proxy..."
nginx -g 'daemon off;' -c "$REPO_ROOT/docker/nginx/nginx.local.conf" -p "$REPO_ROOT" > logs/nginx.log 2>&1 &
NGINX_PID=$!
./scripts/wait-for-port.sh 1000 10 "Nginx" || {
    echo "  See logs/nginx.log for details"
    tail -10 logs/nginx.log
    cleanup
}
echo "✓ Nginx started on localhost:1000"

# ── Ready ─────────────────────────────────────────────────────────────────────

echo ""
echo "=========================================="
if $DEV_MODE; then
    echo "  ✓ MedrixFlow development server is running!"
else
    echo "  ✓ MedrixFlow production server is running!"
fi
echo "=========================================="
echo ""
echo "  🌐 Application: http://localhost:1000"
echo "  📡 API Gateway: http://localhost:1000/api/*"
echo "  🤖 LangGraph:   http://localhost:1000/api/langgraph/*"
echo ""
echo "  📋 Logs:"
echo "     - LangGraph: logs/langgraph.log"
echo "     - Gateway:   logs/gateway.log"
echo "     - Frontend:  logs/frontend.log"
echo "     - Nginx:     logs/nginx.log"
echo ""
echo "Press Ctrl+C to stop all services"

wait
