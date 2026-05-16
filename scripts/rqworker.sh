#!/bin/bash
set -e

PUID=${PUID:-1000}
PGID=${PGID:-1000}

# Wait for Redis to be ready
sleep 2

if [ "$PUID" != "0" ]; then
    groupadd -g "$PGID" -o easyenc 2>/dev/null || true
    useradd -u "$PUID" -g "$PGID" -o -m -s /bin/bash easyenc 2>/dev/null || true
    exec su -s /bin/bash easyenc -c "python3 manage.py rqworker default"
else
    exec python3 manage.py rqworker default
fi
