import os
import sys
from pathlib import Path

# Add the 'quizapp' directory to the Python path to reach 'quiz_project'
current_path = Path(__file__).parent.resolve()
sys.path.append(str(current_path / "quizapp"))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quiz_project.settings')

try:
    from django.core.wsgi import get_wsgi_application
    # Export 'application' and 'app' for various deployment platforms
    application = get_wsgi_application()
    app = application
except Exception as e:
    print(f"Error loading Django application: {e}")
    raise e
