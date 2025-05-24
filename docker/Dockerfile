FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create directory for credentials
RUN mkdir -p /root/.grekko

# Copy requirements
COPY requirements.txt .
COPY tests/test_requirements.txt ./tests/test_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r tests/test_requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create directory for logs
RUN mkdir -p /app/logs

# Default command
CMD ["python", "src/main.py"]