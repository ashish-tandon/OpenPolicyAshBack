# Multi-stage Dockerfile for OpenPolicy with Dashboard
FROM node:18-alpine AS dashboard-builder

# Set working directory for dashboard
WORKDIR /app/dashboard

# Copy dashboard package files
COPY dashboard/package*.json ./

# Install dashboard dependencies
RUN npm ci

# Copy dashboard source code
COPY dashboard/ ./

# Build dashboard
RUN npm run build

# Python API stage
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///./openpolicy.db
ENV NODE_ENV=production

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY scrapers/ ./scrapers/
COPY regions_report.json .
COPY policies/ ./policies/

# Copy built dashboard from previous stage
COPY --from=dashboard-builder /app/dashboard/dist ./dashboard/dist

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create startup script
RUN echo '#!/bin/bash\n\
echo "🚀 Starting OpenPolicy with Dashboard..."\n\
echo "📅 $(date)"\n\
\n\
# Initialize database schema\n\
echo "📝 Initializing database schema..."\n\
python -c "from src.database.models import Base; from src.database.config import engine; Base.metadata.create_all(bind=engine); print(\"Database schema created\")" || {\n\
    echo "❌ Failed to initialize database schema"\n\
    exit 1\n\
}\n\
\n\
# Start nginx in background\n\
echo "🌐 Starting Nginx..."\n\
nginx\n\
\n\
# Start FastAPI server\n\
echo "🎯 Starting FastAPI server..."\n\
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload\n\
' > /app/start.sh && chmod +x /app/start.sh

# Create health check script
RUN echo '#!/bin/bash\n\
# Health check for the API\n\
if ! curl -f http://localhost:8000/health >/dev/null 2>&1; then\n\
    echo "API is not responding"\n\
    exit 1\n\
fi\n\
echo "API is healthy"\n\
exit 0\n\
' > /app/healthcheck.sh && chmod +x /app/healthcheck.sh

# Expose ports
EXPOSE 80 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /app/healthcheck.sh

# Start the application
CMD ["/app/start.sh"] 