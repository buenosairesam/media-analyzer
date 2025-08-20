FROM python:3.11-slim

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
COPY --chown=appuser:appuser docker-entrypoint.sh /app/

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Default command (can be overridden for celery workers)
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["web"]