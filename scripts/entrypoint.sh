#!/bin/bash
set -e

PUID=${PUID:-1000}
PGID=${PGID:-1000}

# Create group and user if not root
if [ "$PUID" != "0" ]; then
    groupadd -g "$PGID" -o easyenc 2>/dev/null || true
    useradd -u "$PUID" -g "$PGID" -o -m -s /bin/bash easyenc 2>/dev/null || true
    chown -R "$PUID":"$PGID" /app/data
    RUN_AS="easyenc"
else
    RUN_AS="root"
fi

# Run migrations
if [ "$RUN_AS" = "root" ]; then
    python3 manage.py migrate --run-syncdb
    python3 manage.py loaddata initial_profiles.json 2>/dev/null || true
    exec python3 manage.py runserver 0.0.0.0:8000
else
    su -s /bin/bash "$RUN_AS" -c "python3 manage.py migrate --run-syncdb"
    su -s /bin/bash "$RUN_AS" -c "python3 manage.py loaddata initial_profiles.json 2>/dev/null || true"
    exec su -s /bin/bash "$RUN_AS" -c "python3 manage.py runserver 0.0.0.0:8000"
fi
