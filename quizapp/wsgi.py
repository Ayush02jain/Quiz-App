import os
from django.core.wsgi import get_wsgi_application

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')

# Get the WSGI application
application = get_wsgi_application()

# Some platforms look for 'app' while others look for 'application'
app = application
