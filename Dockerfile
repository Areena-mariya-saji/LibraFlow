# ==============================================================================
# LibraFlow — Library Management System
# Production Multi-Stage Dockerfile for Python Flask & Gunicorn
# ==============================================================================

FROM python:3.12-slim

# Set environment variables for Python in containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5000 \
    DATABASE_PATH=/app/data/libraflow.db

# Set working directory
WORKDIR /app

# Install system dependencies (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements (including gunicorn on Linux)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn>=21.2.0

# Create a non-privileged user and directory for persistent database
RUN useradd -m -u 1000 libraflow && \
    mkdir -p /app/data && \
    chown -R libraflow:libraflow /app

# Copy application source code
COPY --chown=libraflow:libraflow . /app/

# Switch to non-root user for security best practices
USER libraflow

# Initialize database schema and initial seed data if not present on container start
RUN python database/seed_data.py

# Expose web service port
EXPOSE 5000

# Docker Healthcheck targeting the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Launch production WSGI application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
