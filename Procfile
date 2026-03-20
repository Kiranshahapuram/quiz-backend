web: python manage.py migrate --noinput && daphne config.asgi:application --port $PORT --bind 0.0.0.0
worker: C_FORCE_ROOT=true celery -A config worker --loglevel=info --concurrency=2
