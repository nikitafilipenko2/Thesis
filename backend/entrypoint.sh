#!/usr/bin/env sh
set -eu

if [ "${POSTGRES_ENABLED:-False}" = "True" ]; then
  python - <<'PY'
import os
import time

import psycopg

host = os.getenv("POSTGRES_HOST", "db")
port = int(os.getenv("POSTGRES_PORT", "5432"))
dbname = os.getenv("POSTGRES_DB", "thesis")
user = os.getenv("POSTGRES_USER", "thesis")
password = os.getenv("POSTGRES_PASSWORD", "")

for _ in range(60):
    try:
        psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        ).close()
        break
    except Exception:
        time.sleep(2)
else:
    raise SystemExit("PostgreSQL is not available")
PY
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn backend.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 300
