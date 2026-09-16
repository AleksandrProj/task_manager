FROM python:3.13-slim

ARG NAME_PROJECT=app
ARG LOCALE_PROJECT=backend

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Set project working directory
WORKDIR /${NAME_PROJECT}

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy code
COPY ${LOCALE_PROJECT}/ /${NAME_PROJECT}

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=${LOCALE_PROJECT}/uv.lock,target=/${NAME_PROJECT}/uv.lock \
    --mount=type=bind,source=${LOCALE_PROJECT}/pyproject.toml,target=/${NAME_PROJECT}/pyproject.toml \
    uv sync --locked --no-install-project --no-editable

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

# Collect static
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Run app
CMD set -xe; python manage.py migrate --no-input; python manage.py runserver 0.0.0.0:8000