#!/bin/sh
# KCK container entrypoint.
#   1. Wait for the DB (if an external DB is configured — no-op for SQLite)
#   2. Run migrations
#   3. Collect static files (idempotent)
#   4. Optionally create a superuser from env vars
#   5. Exec the CMD
set -e

echo "==> KCK entrypoint starting"
echo "    DJANGO_SETTINGS_MODULE = $DJANGO_SETTINGS_MODULE"
echo "    DEBUG = ${DEBUG:-(unset)}"

# --- Optional Postgres wait ------------------------------------------------
if [ -n "$POSTGRES_HOST" ]; then
    echo "==> Waiting for Postgres at ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}..."
    for i in $(seq 1 30); do
        if python -c "import socket,sys,os; s=socket.socket(); s.settimeout(2); s.connect((os.environ['POSTGRES_HOST'], int(os.environ.get('POSTGRES_PORT','5432')))); s.close()" 2>/dev/null; then
            echo "    Postgres is up."
            break
        fi
        [ "$i" -eq 30 ] && { echo "    Postgres never came up."; exit 1; }
        sleep 1
    done
fi

# --- Migrations ------------------------------------------------------------
echo "==> Running migrations..."
python manage.py migrate --noinput

# --- Collect static --------------------------------------------------------
echo "==> Collecting static files..."
python manage.py collectstatic --noinput --clear

# --- Optional: create superuser from env -----------------------------------
# Only runs when DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD are all set.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "==> Ensuring superuser '$DJANGO_SUPERUSER_USERNAME' exists..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
U = get_user_model()
u, created = U.objects.get_or_create(
    username='$DJANGO_SUPERUSER_USERNAME',
    defaults={'email': '$DJANGO_SUPERUSER_EMAIL', 'is_superuser': True, 'is_staff': True})
u.email = '$DJANGO_SUPERUSER_EMAIL'
u.is_superuser = True; u.is_staff = True
u.set_password('$DJANGO_SUPERUSER_PASSWORD')
u.save()
print('    created' if created else '    updated', 'superuser', u.username)
"
fi

echo "==> Starting: $@"
exec "$@"
