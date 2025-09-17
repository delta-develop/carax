# Makefile to manage the Carax project with Docker Compose

# Variables
API_URL := http://localhost:8000
DASHBOARDS_URL := http://localhost:5601

# Commands to open URLs (tries to be compatible with Linux, macOS, and Windows)
OPEN_CMD := xdg-open
ifeq ($(shell uname -s),Darwin)
	OPEN_CMD := open
else ifeq ($(findstring Microsoft,$(shell uname -r)),Microsoft)
	OPEN_CMD := start
endif

.PHONY: help up run down build build-app open-api open-dashboards logs logs-app ps restart rebuild fucking_nuke setup shell install clean test start venv psql rebuild-app

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Core targets:"
	@echo "  install           Install requirements (with tool checks)."
	@echo "  test              Run tests."
	@echo "  run               Run the service and dependencies in Docker."
	@echo "  down              Teardown running services."
	@echo "  clean             Teardown and remove containers/volumes."
	@echo ""
	@echo "Extra targets:"
	@echo "  up                Starts all services in the background."
	@echo "  build             Builds or rebuilds service images (especially 'app')."
	@echo "  build-app         Specifically builds the 'app' service image."
	@echo "  logs              Shows logs for all services."
	@echo "  logs-app          Shows logs for the 'app' service."
	@echo "  ps                Lists running containers."
	@echo "  restart           Restarts all services (down + up)."
	@echo "  rebuild           Rebuilds the 'app' image and restarts all services."
	@echo "  setup             Initialize database schema inside the app container."
	@echo "  shell             Open an interactive shell in the 'app' container."

# Start all services
up:
	@echo "Starting all services..."
	docker-compose -f docker-compose.yml up -d

# Run service and dependencies (build then up)
run: build-up

# Stop all services
down:
	@echo "Stopping all services..."
	docker-compose -f docker-compose.yml down

# Build all images (if changed)
build: build-app

# Build the Python application image
build-app:
	@echo "Building the 'app' service image..."
	docker-compose -f docker-compose.yml build app


# Additional useful commands
logs:
	docker-compose -f docker-compose.yml logs -f

logs-app:
	docker-compose -f docker-compose.yml logs -f app

ps:
	docker-compose -f docker-compose.yml ps

restart: down up

rebuild: build-app down up

.PHONY: fucking_nuke

# Use under your own risk, this will clean EVERYTHING in your docker, so be careful.
fucking_nuke:
	@echo "⚠️  Ejecutando nuke total de Docker..."; \
	docker rm -f $$(docker ps -aq) 2>/dev/null || true; \
	docker rmi -f $$(docker images -aq) 2>/dev/null || true; \
	docker volume rm -f $$(docker volume ls -q) 2>/dev/null || true; \
	docker network rm $$(docker network ls -q | grep -v -E "bridge|host|none") 2>/dev/null || true; \
	docker builder prune -af -f; \
	echo "🔥 Docker ha sido completamente aniquilado."

build-up:
	docker-compose -f docker-compose.yml build && docker-compose -f docker-compose.yml up -d

# Run setup script to initialize databases and indices
setup:
	@echo "Running setup script to initialize databases..."
	docker-compose -f docker-compose.yml exec app python3 -m app.setup

shell:
	docker-compose -f docker-compose.yml exec app /bin/bash
venv:
	@echo "Activating virtual environment..."
	. venv/bin/activate && exec $$SHELL

psql:
	docker-compose -f docker-compose.yml exec postgres psql -U carax -d db

rebuild-app:
	docker-compose -f docker-compose.yml build app
	docker-compose -f docker-compose.yml up -d app

start: build-up

test:
	PYTHONPATH=. coverage run -m pytest -vvv tests/
	coverage report -m

install:
	@# Check required tools and provide install guidance if missing
	@if ! command -v docker >/dev/null 2>&1; then \
		echo "[!] docker is not installed."; \
		echo "    macOS:   brew install --cask docker && open -a Docker"; \
		echo "    Ubuntu:  sudo apt-get update && sudo apt-get install docker.io"; \
		exit 1; \
	fi
	@if ! command -v docker-compose >/dev/null 2>&1; then \
		echo "[!] docker-compose not found."; \
		echo "    Option A: Install Docker Desktop (includes compose)."; \
		echo "    Option B: pipx install docker-compose OR brew install docker-compose"; \
		exit 1; \
	fi
	@if ! command -v python3 >/dev/null 2>&1; then \
		echo "[!] python3 is not installed."; \
		echo "    macOS:   brew install python"; \
		echo "    Ubuntu:  sudo apt-get install -y python3 python3-venv"; \
		exit 1; \
	fi
	@if ! command -v pip >/dev/null 2>&1; then \
		echo "[!] pip not found; using python -m pip"; \
		python3 -m ensurepip --upgrade || true; \
	fi
	python3 -m pip install --upgrade pip
	python3 -m pip install -r requirements.txt

clean:
	@echo "Stopping and removing containers, networks, and volumes..."
	docker-compose -f docker-compose.yml down -v || true
