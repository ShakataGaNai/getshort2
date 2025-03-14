FROM python:3.12-slim

# Build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VCS_URL
ARG VERSION

# Labels
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.title="GetShort URL Shortener" \
      org.opencontainers.image.description="A simple and powerful URL shortener service" \
      org.opencontainers.image.url="https://github.com/ShakataGaNai/getshort2" \
      org.opencontainers.image.source="${VCS_URL}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.authors="GetShort Maintainers" \
      org.opencontainers.image.vendor="GetShort" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Install dependencies and curl for health checks
RUN apt-get update && apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOG_TO_STDOUT=true

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Define health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/health/ready || exit 1

# Run the application with Gunicorn
CMD gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 2 "run:app"