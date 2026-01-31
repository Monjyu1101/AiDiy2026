# Multi-stage build for AiDiy2026
# Stage 1: Backend dependencies
FROM python:3.13-slim as backend-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend pyproject.toml
COPY backend_server/pyproject.toml /app/backend_server/

# Install Python dependencies from pyproject.toml
WORKDIR /app/backend_server
RUN pip install --no-cache-dir .

# Stage 2: Frontend build
FROM node:20-alpine as frontend-builder

WORKDIR /app/frontend_server

# Copy package files
COPY frontend_server/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend_server/ ./

# Build frontend
RUN npm run build

# Stage 3: Final runtime image
FROM python:3.13-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=backend-builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend application
COPY backend_server/ /app/backend_server/

# Copy built frontend files
COPY --from=frontend-builder /app/frontend_server/dist /app/frontend_server/dist
COPY --from=frontend-builder /app/frontend_server/public /app/frontend_server/public

# Create necessary directories
RUN mkdir -p /app/temp /app/_data

# Expose ports
# 8090: Frontend
# 8091: Backend Core API (main1)
# 8092: Backend Apps API (main2)
EXPOSE 8090 8091 8092

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8091/docs || exit 1

# Start script
COPY docker/start.sh /app/
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]