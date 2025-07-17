
import sys
import os

os.environ.setdefault('SESSION_SECRET', 'pythonanywhere-production-secret-key-change-this')

os.environ.setdefault('FLASK_ENV', 'production')

from app import app as application

if not hasattr(application, '_pythonanywhere_configured'):
    application.config.update({
        'SERVER_NAME': None,
        'APPLICATION_ROOT': '/',
        'PREFERRED_URL_SCHEME': 'https'
    })
    application._pythonanywhere_configured = True

if __name__ == "__main__":
    application.run(debug=False)