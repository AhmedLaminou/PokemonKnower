#!/bin/bash

# Docker entrypoint script for Pokemon Knower

set -e

echo "🚀 Starting Pokemon Knower..."

# Create uploads directory if it doesn't exist
mkdir -p static/uploads

# Check if required files exist
if [ ! -f "Data/pokémon_with_stats/All_Pokemon.csv" ]; then
    echo "❌ Error: Data/pokémon_with_stats/All_Pokemon.csv not found!"
    exit 1
fi


if [ ! -f "class_indices.json" ]; then
    echo "❌ Error: class_indices.json not found!"
    exit 1
fi

# Start Flask with Gunicorn for production
echo "📦 Starting Flask with Gunicorn..."

# Initialize database tables before starting workers
echo "🗃️ Initializing database..."
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('✅ Database initialized')"

exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers 4 \
    --threads 2 \
    --worker-class gthread \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload \
    app:app
