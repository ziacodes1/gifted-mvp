#!/bin/sh
# Settings fail closed here if the production configuration is unsafe (see config/security.py).
set -e
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  python manage.py migrate --noinput
fi
python manage.py collectstatic --noinput --verbosity 0
exec "$@"
