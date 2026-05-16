#!/bin/bash
set -e

# Wait for Redis to be ready
sleep 2

# Start RQ worker
exec python3 manage.py rqworker default
