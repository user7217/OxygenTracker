# wsgi.py - PythonAnywhere WSGI configuration file for MySQL
import sys
import os

# Add your project directory to the Python path
path = '/home/yourusername/mysite'  # Replace 'yourusername' with your PythonAnywhere username
if path not in sys.path:
    sys.path.append(path)

# Set environment variables for production
os.environ['SESSION_SECRET'] = 'your-production-secret-key-here'  # Replace with a secure secret key
os.environ['FLASK_ENV'] = 'production'
os.environ['DATABASE_URL'] = 'mysql://yourusername:yourpassword@yourusername.mysql.pythonanywhere-services.com/yourusername$databasename'

# Import your Flask application (using MySQL version)
from app_mysql import app as application

if __name__ == "__main__":
    application.run()