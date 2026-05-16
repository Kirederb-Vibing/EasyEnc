#!/bin/bash
set -e

# Run migrations
python3 manage.py migrate --run-syncdb

# Load initial data if available
python3 manage.py loaddata initial_profiles.json 2>/dev/null || true

# Start Django dev server
exec python3 manage.py runserver 0.0.0.0:8000
