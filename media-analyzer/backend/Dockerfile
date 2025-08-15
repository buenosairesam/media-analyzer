FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies  
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Start development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]