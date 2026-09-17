.PHONY: env up down build restart logs db run test lint lint-fix format format-check

ENV_FILE := .env
ENV_EXAMPLE := .env.example
COMPOSE_FILE := ../docker/docker-compose.yml
COMPOSE = docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE)
TEST_DB_HOST ?= 127.0.0.1
TEST_ARGS ?= -v

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
	$(COMPOSE) up -d --build

# Stop containers
down:
	$(COMPOSE) down

# Build images
build: env
	$(COMPOSE) build

# Restart containers
restart: env
	$(COMPOSE) up -d --build --force-recreate

# Logs containers
logs:
	$(COMPOSE) logs -f

# Start PostgreSQL and wait until it accepts connections
db: env
	$(COMPOSE) up -d --wait postgres

# Run Django locally using APP_PORT from .env (PostgreSQL must be running)
run: env
	uv run --locked python manage.py migrate --no-input
	uv run --locked --env-file $(ENV_FILE) sh -c \
		'exec python manage.py runserver 127.0.0.1:$${APP_PORT:-8000}'

# Run tests against a separate PostgreSQL test database
test:
	DB_HOST="$(TEST_DB_HOST)" uv run --locked pytest $(TEST_ARGS)

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
