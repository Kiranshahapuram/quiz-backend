web: daphne config.asgi:application --port $PORT --bind 0.0.0.0
worker: celery -A config worker --loglevel=info
