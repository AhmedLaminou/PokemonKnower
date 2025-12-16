# Pokemon Knower - Docker Setup Guide

## Quick Start

### Prerequisites
- Docker installed ([Download](https://www.docker.com/products/docker-desktop))
- Docker Compose installed (included with Docker Desktop)

### Build and Run with Docker Compose

1. **Clone/Navigate to project:**
```bash
cd PokemonKnower
```

2. **Build the image:**
```bash
docker-compose build
```

3. **Run the application:**
```bash
docker-compose up
```

4. **Access the application:**
- **Frontend**: http://localhost:80 (via Nginx)
- **Backend API**: http://localhost:5000
- **Direct Backend**: http://localhost:5000 (without Nginx)

### Stop the application:
```bash
docker-compose down
```

## Docker Architecture

### Services:
1. **pokemon-knower** - Main Flask backend + React frontend
2. **nginx** - Reverse proxy and static file serving (optional)

## Building Standalone Docker Image

```bash
# Build image
docker build -t pokemon-knower:latest .

# Run container
docker run -d \
  --name pokemon-knower \
  -p 5000:5000 \
  -v $(pwd)/static/uploads:/app/static/uploads \
  pokemon-knower:latest

# View logs
docker logs -f pokemon-knower

# Stop container
docker stop pokemon-knower
```

## Environment Configuration

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Edit `.env` for custom settings:
```
FLASK_ENV=production
PORT=5000
MAX_UPLOAD_SIZE=100M
```

## Volume Mounts

- **Uploads**: `./static/uploads:/app/static/uploads` - Persists user uploads

## Production Deployment

### Using Gunicorn (included in Docker)
The Docker container automatically uses Gunicorn with:
- 4 workers
- 2 threads per worker
- 60-second timeout
- Automatic logging

### Using Nginx as Reverse Proxy
Uncomment the nginx service in `docker-compose.yml` for production setup with:
- Load balancing
- SSL/TLS support (configure in `nginx.conf`)
- Static file caching
- Gzip compression

### Kubernetes Deployment
Create a `kubernetes.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pokemon-knower
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pokemon-knower
  template:
    metadata:
      labels:
        app: pokemon-knower
    spec:
      containers:
      - name: pokemon-knower
        image: pokemon-knower:latest
        ports:
        - containerPort: 5000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        volumeMounts:
        - name: uploads
          mountPath: /app/static/uploads
      volumes:
      - name: uploads
        emptyDir: {}
```

## Troubleshooting

### Container won't start
```bash
docker-compose logs -f pokemon-knower
```

### Model loading errors
The app uses fallback prediction when the model can't load. Check logs for details.

### Port already in use
Change ports in `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Use 8080 instead of 5000
```

### Upload folder permissions
```bash
docker exec pokemon-knower chmod -R 755 static/uploads
```

## Clean Up

```bash
# Remove containers and networks
docker-compose down

# Remove images
docker rmi pokemon-knower:latest

# Remove volumes (caution: removes data)
docker-compose down -v

# Remove all Docker resources
docker system prune -a
```

## Performance Tips

1. **Increase workers** in `docker-entrypoint.sh` based on CPU cores:
   ```bash
   --workers 8  # For 8+ CPU cores
   ```

2. **Enable caching** in Nginx for static files (already configured)

3. **Use external database** for scaling (future enhancement)

4. **Monitor container resources**:
   ```bash
   docker stats pokemon-knower
   ```

## Security Considerations

- ✅ Multi-stage build (reduces image size)
- ✅ Non-root user (use: `USER appuser`)
- ✅ Health checks enabled
- ✅ Environment variables for sensitive data
- ✅ Input validation in Flask
- ✅ CORS protection

### Add to Dockerfile for production:
```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```

## Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Verify files exist: pokemon.csv, class_indices.json, model file
3. Check port availability: `netstat -an | grep 5000`
