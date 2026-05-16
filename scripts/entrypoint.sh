#!/bin/bash
set -e

PUID=${PUID:-1000}
PGID=${PGID:-1000}

# Create group and user if not root
if [ "$PUID" != "0" ]; then
    groupadd -g "$PGID" -o easyenc 2>/dev/null || true
    useradd -u "$PUID" -g "$PGID" -o -m -s /bin/bash easyenc 2>/dev/null || true
    chown -R "$PUID":"$PGID" /app/data
fi

# Run migrations with flock to prevent race between web and worker
run_cmd() {
    if [ "$PUID" != "0" ]; then
        su -s /bin/bash easyenc -c "$1"
    else
        bash -c "$1"
    fi
}

flock /app/data/.migrate.lock -c "$(cat <<'SCRIPT'
python3 manage.py migrate --run-syncdb 2>/dev/null
python3 manage.py loaddata initial_profiles.json 2>/dev/null || true
SCRIPT
)"

# Execute CMD (passed as arguments to entrypoint)
if [ "$PUID" != "0" ]; then
    exec gosu easyenc "$@"
else
    exec "$@"
fi
