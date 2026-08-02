#!/bin/sh
set -e

echo "Waiting for database at ${DB_HOST}:${DB_PORT}..."
python - <<'EOF'
import os
import socket
import time

host = os.getenv('DB_HOST', 'postgres')
port = int(os.getenv('DB_PORT', '5432'))
timeout = int(os.getenv('DB_WAIT_TIMEOUT', '60'))

deadline = time.time() + timeout
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=5):
            print('Database is ready.')
            break
    except OSError:
        print('Database not ready, retrying...')
        time.sleep(2)
else:
    print('ERROR: Database did not become ready in time.')
    exit(1)
EOF

echo "Starting: $*"
exec "$@"
