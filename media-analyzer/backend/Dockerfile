FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies for AI processing and media handling
RUN apt-get update && apt-get install -y \
    postgresql-client \
    ffmpeg \
    libgl1-mesa-dri \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies  
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy source code and set ownership in one layer
COPY --chown=appuser:appuser . .

# Copy entrypoint scripts
COPY --chown=appuser:appuser entrypoint-web.sh /app/
COPY --chown=appuser:appuser entrypoint-celery.sh /app/

# Make entrypoint scripts executable
RUN chmod +x entrypoint-web.sh entrypoint-celery.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Development stage
FROM base AS development
ENV DJANGO_DEBUG=1
CMD ["./entrypoint-web.sh"]

# Production stage  
FROM base AS production
ENV DJANGO_DEBUG=0
CMD ["./entrypoint-web.sh"]