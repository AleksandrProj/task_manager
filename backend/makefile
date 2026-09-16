.PHONY: env up down build restart logs

ENV_FILE := .env
ENV_EXAMPLE := .env.example
COMPOSE_FILE := ../docker/docker-compose.yml

# Create .env from .env.example
env:
	@if [ ! -f $(ENV_FILE) ]; then \
		cp $(ENV_EXAMPLE) $(ENV_FILE); \
		echo "Created $(ENV_FILE)"; \
	else \
		echo "$(ENV_FILE) already exists"; \
	fi

# Run containers
up: env
	docker compose -f $(COMPOSE_FILE) up -d

# Stop containers
down:
	docker compose -f $(COMPOSE_FILE) down

# Build images
build: env
	docker compose -f $(COMPOSE_FILE) build

# Restart containers
restart: env
	docker compose -f $(COMPOSE_FILE) down
	docker compose -f $(COMPOSE_FILE) up -d --build

# Logs containers
logs:
	docker compose -f $(COMPOSE_FILE) logs -f

# RUFF
# Lint check
lint:
	ruff check .

# Lint fix
lint-fix:
	ruff check . --fix

# Lint format
format:
	ruff format .

# Lint format and check
format-check:
	ruff format --check .