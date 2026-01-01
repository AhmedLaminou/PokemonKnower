# Dockerfile for Pokemon Knower - Flask Application
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python application
COPY app.py .
COPY models.py .
COPY auth.py .
COPY admin.py .
COPY donations.py .
COPY migrate_db.py .
COPY pokemon.csv .
COPY class_indices.json .
COPY pokemon_classifier_model_V3.h5 .

# Copy templates and static files
COPY templates/ ./templates/
COPY static/ ./static/

# Copy entrypoint script
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose ports
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/')"

# Run entrypoint
ENTRYPOINT ["/entrypoint.sh"]
