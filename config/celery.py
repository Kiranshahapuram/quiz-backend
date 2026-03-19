import os
import warnings
from celery import Celery

# Force root access allowed (required for some containerized environments like Railway)
os.environ.setdefault('C_FORCE_ROOT', 'true')
# Suppress the persistent security warning about superuser privileges
warnings.filterwarnings("ignore", message=".*superuser privileges.*")

# We don't hardcode local here so Railway environment variables take precedence.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

