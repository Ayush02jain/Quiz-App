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
    from django.core.management import call_command

    # Export 'application' and 'app' for various deployment platforms
    application = get_wsgi_application()
    app = application

    # Vercel-specific: If we are on Vercel, ensure the temporary DB is migrated
    if os.environ.get('VERCEL'):
        # Only run migrations once when the /tmp/db.sqlite3 is created
        # The copy logic is already in settings.py, which runs before this
        db_path = Path('/tmp/db.sqlite3')
        # We use a marker file to ensure we don't migrate on every single request
        marker = Path('/tmp/db_migrated')
        if not marker.exists():
            print("Running migrations for serverless SQLite...")
            call_command('migrate', interactive=False)
            marker.touch()

except Exception as e:
    print(f"Error loading Django application: {e}")
    raise e
