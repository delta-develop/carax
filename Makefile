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
	@echo "Available targets:"
	@echo "  up                Starts all services in the background."
	@echo "  run               Alias for 'up'."
	@echo "  down              Stops and removes all containers, networks, and (optionally) volumes."
	@echo "  build             Builds or rebuilds service images (especially 'app')."
	@echo "  build-app         Specifically builds the 'app' service image."
	@echo "  open-api          Opens the API URL (${API_URL}) in the default browser."
	@echo "  open-dashboards   Opens the OpenSearch Dashboards URL (${DASHBOARDS_URL}) in the default browser."
	@echo "  logs              Shows logs for all services."
	@echo "  logs-app          Shows logs for the 'app' service."
	@echo "  ps                Lists running containers."
	@echo "  restart           Restarts all services (down + up)."
	@echo "  rebuild           Rebuilds the 'app' image and restarts all services."
	@echo "  setup             Runs the setup script to initialize databases and indices."
	@echo "  shell             Opens an interactive shell in the 'app' service container."
	@echo "  install           Installs Python requirements locally."
	@echo "  test              Runs tests with coverage."
	@echo "  clean             Tear down and remove containers and dangling resources."

# Start all services
up:
	@echo "Starting all services..."
	docker-compose -f docker-compose.yml up -d

# Alias for up
run: up

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
	docker-compose -f docker-compose.yml exec postgres psql -U carax -d conversations

rebuild-app:
	docker-compose -f docker-compose.yml build app
	docker-compose -f docker-compose.yml up -d app

start: build-up

test:
	PYTHONPATH=. coverage run -m pytest -vvv tests/
	coverage report -m

install:
	pip install --upgrade pip
	pip install -r requirements.txt

clean:
	@echo "Stopping and removing containers, networks, and volumes..."
	docker-compose -f docker-compose.yml down -v || true
