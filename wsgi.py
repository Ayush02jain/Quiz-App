import os
import sys
from pathlib import Path

# Add the 'quizapp' directory to the Python path to reach 'quiz_project'
current_path = Path(__file__).parent
sys.path.append(str(current_path / "quizapp"))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')

from django.core.wsgi import get_wsgi_application

# Export 'application' and 'app' for various deployment platforms
application = get_wsgi_application()
app = application
