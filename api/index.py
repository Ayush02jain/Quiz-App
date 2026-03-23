import os
import sys
from pathlib import Path

# Add the 'quizapp' directory to the Python path to reach 'quiz_project'
current_path = Path(__file__).parent.parent
sys.path.append(str(current_path / "quizapp"))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')

from django.core.wsgi import get_wsgi_application

# Vercel needs 'app' to be exported in its entrypoint
app = get_wsgi_application()
