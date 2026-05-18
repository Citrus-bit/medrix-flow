# Anaxa - Unified Development Environment

.PHONY: help bootstrap config setup doctor config-upgrade check install verify release-check dev dev-daemon start stop up down clean clean-cache docker-init docker-start docker-stop docker-logs docker-logs-frontend docker-logs-gateway

PYTHON ?= python3

help:
	@echo "Anaxa Development Commands:"
	@echo "  make bootstrap       - First-time setup: check tools, create local config, install dependencies"
	@echo "  make config          - Generate local config files (aborts if config already exists)"
	@echo "  make setup           - Idempotent local setup wizard (creates missing config/env files)"
	@echo "  make doctor          - Validate config, env vars, sandbox prerequisites, and DB writability"
	@echo "  make config-upgrade  - Merge new fields from config.example.yaml into config.yaml"
	@echo "  make check           - Check if all required tools are installed"
	@echo "  make install         - Install all dependencies (frontend + backend dev group)"
	@echo "  make verify          - Run local checks aligned with CI (backend lint/test + frontend lint/typecheck)"
	@echo "  make release-check   - Check that local secrets/runtime data are not tracked or staged"
	@echo "  make dev             - Start all services in development mode (with hot-reloading)"
	@echo "  make dev-daemon      - Start all services in background (daemon mode)"
	@echo "  make start           - Start all services in production mode (optimized, no hot-reloading)"
	@echo "  make stop            - Stop all running services"
	@echo "  make clean           - Clean up processes and temporary files"
	@echo "  make clean-cache     - Remove safe regenerated caches, keep local data and dependencies"
	@echo ""
	@echo "Docker Production Commands:"
	@echo "  make up              - Build and start production Docker services (localhost:6200)"
	@echo "  make down            - Stop and remove production Docker containers"
	@echo ""
	@echo "Docker Development Commands:"
	@echo "  make docker-init     - Pull the sandbox image"
	@echo "  make docker-start    - Start Docker services (mode-aware from config.yaml, localhost:6200)"
	@echo "  make docker-stop     - Stop Docker development services"
	@echo "  make docker-logs     - View Docker development logs"
	@echo "  make docker-logs-frontend - View Docker frontend logs"
	@echo "  make docker-logs-gateway - View Docker gateway logs"

bootstrap:
	@echo "=========================================="
	@echo "  Anaxa First-Time Bootstrap"
	@echo "=========================================="
	@echo ""
	@$(PYTHON) ./scripts/check.py
	@echo ""
	@cd backend && uv run python ../scripts/setup_wizard.py
	@echo ""
	@$(MAKE) install
	@echo ""
	@echo "=========================================="
	@echo "  ✓ Bootstrap complete"
	@echo "=========================================="
	@echo "Next:"
	@echo "  1. make dev"
	@echo "  2. Open http://localhost:6200"
	@echo "  3. Configure your model/API keys in Settings & More -> Setup"

config:
	@$(PYTHON) ./scripts/configure.py

setup:
	@cd backend && uv run python ../scripts/setup_wizard.py

doctor:
	@cd backend && uv run python ../scripts/doctor.py

config-upgrade:
	@./scripts/config-upgrade.sh

# Check required tools
check:
	@$(PYTHON) ./scripts/check.py

# Install all dependencies
install:
	@echo "Installing backend dependencies..."
	@cd backend && uv sync --group dev
	@echo "Installing frontend dependencies..."
	@cd frontend && pnpm install
	@echo "✓ All dependencies installed"
	@echo ""
	@echo "=========================================="
	@echo "  Optional: Pre-pull Sandbox Image"
	@echo "=========================================="
	@echo ""
	@echo "If you plan to use Docker/Container-based sandbox, you can pre-pull the image:"
	@echo "  make setup-sandbox"
	@echo ""

verify:
	@echo "Running backend checks (lint + test)..."
	@cd backend && make lint && make test
	@echo "Running frontend checks (lint + typecheck + unit tests)..."
	@cd frontend && pnpm lint && pnpm typecheck && pnpm test:unit
	@echo "Running frontend build check..."
	@cd frontend && BETTER_AUTH_SECRET=local-dev-secret pnpm build
	@echo "✓ Verification checks passed"

release-check:
	@$(PYTHON) ./scripts/release_check.py

# Pre-pull sandbox Docker image (optional but recommended)
setup-sandbox:
	@echo "=========================================="
	@echo "  Pre-pulling Sandbox Container Image"
	@echo "=========================================="
	@echo ""
	@IMAGE=$$(grep -A 20 "# sandbox:" config.yaml 2>/dev/null | grep "image:" | awk '{print $$2}' | head -1); \
	if [ -z "$$IMAGE" ]; then \
		IMAGE="enterprise-public-cn-beijing.cr.volces.com/vefaas-public/all-in-one-sandbox:latest"; \
		echo "Using default image: $$IMAGE"; \
	else \
		echo "Using configured image: $$IMAGE"; \
	fi; \
	echo ""; \
	if command -v container >/dev/null 2>&1 && [ "$$(uname)" = "Darwin" ]; then \
		echo "Detected Apple Container on macOS, pulling image..."; \
		container pull "$$IMAGE" || echo "⚠ Apple Container pull failed, will try Docker"; \
	fi; \
	if command -v docker >/dev/null 2>&1; then \
		echo "Pulling image using Docker..."; \
		if docker pull "$$IMAGE"; then \
			echo ""; \
			echo "✓ Sandbox image pulled successfully"; \
		else \
			echo ""; \
			echo "⚠ Failed to pull sandbox image (this is OK for local sandbox mode)"; \
		fi; \
	else \
		echo "✗ Neither Docker nor Apple Container is available"; \
		echo "  Please install Docker: https://docs.docker.com/get-docker/"; \
		exit 1; \
	fi

# Start all services in development mode (with hot-reloading)
dev:
	@./scripts/serve.sh --dev

# Start all services in production mode (with optimizations)
start:
	@./scripts/serve.sh --prod

# Start all services in daemon mode (background)
dev-daemon:
	@./scripts/start-daemon.sh

# Stop all services
stop:
	@echo "Stopping all services..."
	@-pkill -f "langgraph dev" 2>/dev/null || true
	@-pkill -f "uvicorn app.gateway.app:app" 2>/dev/null || true
	@-pkill -f "next dev" 2>/dev/null || true
	@-pkill -f "next start" 2>/dev/null || true
	@-pkill -f "next-server" 2>/dev/null || true
	@-nginx -c $(PWD)/docker/nginx/nginx.local.conf -p $(PWD) -s quit 2>/dev/null || true
	@sleep 1
	@-pkill -9 nginx 2>/dev/null || true
	@-lsof -ti :6203 | xargs kill -9 2>/dev/null || true
	@-lsof -ti :6202 | xargs kill -9 2>/dev/null || true
	@-lsof -ti :6201 | xargs kill -9 2>/dev/null || true
	@echo "Cleaning up sandbox containers..."
	@-./scripts/cleanup-containers.sh medrix-flow-sandbox 2>/dev/null || true
	@echo "✓ All services stopped"

# Clean up safe regenerated caches. This intentionally keeps backend/.medrix-flow,
# backend/.venv, and frontend/node_modules.
clean-cache:
	@echo "Cleaning safe regenerated caches..."
	@-rm -rf frontend/.next 2>/dev/null || true
	@-rm -rf logs 2>/dev/null || true
	@-rm -rf .code-review-graph 2>/dev/null || true
	@-rm -rf backend/.pytest_cache backend/.ruff_cache 2>/dev/null || true
	@-rm -rf frontend/.pytest_cache frontend/.ruff_cache 2>/dev/null || true
	@-find backend frontend scripts -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "Retained: backend/.medrix-flow, backend/.venv, frontend/node_modules"
	@echo "Current size summary:"
	@-du -sh . 2>/dev/null || true
	@-for path in frontend/.next frontend/node_modules backend/.venv backend/.medrix-flow logs .code-review-graph; do \
		if [ -e "$$path" ]; then \
			du -sh "$$path"; \
		else \
			echo "0B	$$path (absent)"; \
		fi; \
	done
	@echo "✓ Cache cleanup complete"

# Clean up
clean: stop clean-cache
	@echo "✓ Cleanup complete"

# ==========================================
# Docker Development Commands
# ==========================================

# Initialize Docker containers and install dependencies
docker-init:
	@./scripts/docker.sh init

# Start Docker development environment
docker-start:
	@./scripts/docker.sh start

# Stop Docker development environment
docker-stop:
	@./scripts/docker.sh stop

# View Docker development logs
docker-logs:
	@./scripts/docker.sh logs

# View Docker development logs
docker-logs-frontend:
	@./scripts/docker.sh logs --frontend
docker-logs-gateway:
	@./scripts/docker.sh logs --gateway

# ==========================================
# Production Docker Commands
# ==========================================

# Build and start production services
up:
	@./scripts/deploy.sh

# Stop and remove production containers
down:
	@./scripts/deploy.sh down
