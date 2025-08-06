# OpenPolicy Merge - Multi-stage Dockerfile
# Builds a single container with FastAPI backend, React frontend, and all services

# =============================================================================
# Stage 1: Python Backend Build
# =============================================================================
FROM python:3.11-slim as python-base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    postgresql-client \
    supervisor \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy Python requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2: Node.js Frontend Build
# =============================================================================
FROM node:18-alpine as frontend-build

WORKDIR /app/frontend

# Copy package files
COPY src/frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy frontend source
COPY src/frontend/ ./

# Build production frontend
RUN npm run build

# =============================================================================
# Stage 3: Production Image
# =============================================================================
FROM python-base as production

# Install additional system packages for production
RUN apt-get update && apt-get install -y \
    supervisor \
    nginx \
    redis-tools \
    curl \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd --create-home --shell /bin/bash app

# Set up directory structure
WORKDIR /app
RUN mkdir -p \
    /app/data \
    /app/logs \
    /app/static \
    /var/log/supervisor \
    /var/log/nginx

# Copy Python application
COPY src/ /app/src/
COPY tests/ /app/tests/
COPY requirements.txt /app/

# Copy built frontend from previous stage
COPY --from=frontend-build /app/frontend/dist /app/static/

# Copy configuration files
COPY docker/supervisord.conf /etc/supervisor/supervisord.conf
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/start.sh /app/start.sh

# Set permissions
RUN chown -R app:app /app && \
    chmod +x /app/start.sh && \
    chmod 755 /app/data /app/logs

# Create nginx directories and set permissions
RUN mkdir -p /var/log/nginx && \
    chown -R app:app /var/log/nginx && \
    chown -R app:app /var/log/supervisor

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Health check script
COPY docker/healthcheck.sh /app/healthcheck.sh
RUN chmod +x /app/healthcheck.sh

# Expose ports
EXPOSE 80 8000 5555 3000

# Set user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /app/healthcheck.sh

# Start application
CMD ["/app/start.sh"]

# =============================================================================
# Development Stage (optional)
# =============================================================================
FROM production as development

USER root

# Install development dependencies
RUN apt-get update && apt-get install -y \
    vim \
    less \
    tree \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    isort \
    flake8 \
    mypy

# Copy development configuration
COPY docker/supervisord.dev.conf /etc/supervisor/supervisord.conf

USER app

# Development command (with hot reload)
CMD ["/app/start.sh", "--dev"]